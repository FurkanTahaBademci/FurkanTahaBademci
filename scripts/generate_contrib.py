#!/usr/bin/env python3
"""Draw the contribution heatmap and streak card from GitHub's own data.

Replaces the third-party streak/activity services: the calendar comes from
the GraphQL contributionsCollection, the SVG is drawn here.
Outputs: assets/contrib-dark.svg, assets/contrib-light.svg
"""

import datetime as dt
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gh  # noqa: E402
import svgkit as kit  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

WEEKS = 53
CELL, GAP = 11, 2
STEP = CELL + GAP
MARGIN_X, GRID_Y = 25, 70
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def from_graphql(year):
    data = gh.graphql(QUERY, {
        "login": gh.USER,
        "from": f"{year}-01-01T00:00:00Z",
        "to": f"{year}-12-31T23:59:59Z",
    })
    if not data:
        return None
    weeks = data["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return {d["date"]: d["contributionCount"]
            for w in weeks for d in w["contributionDays"]}


def from_public_page(year):
    """Parse the public contribution calendar — works without any token."""
    url = (f"https://github.com/users/{gh.USER}/contributions"
           f"?from={year}-01-01&to={year}-12-31")
    req = urllib.request.Request(url, headers={"User-Agent": gh.USER})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError):
        return None

    dates = dict(re.findall(r'data-date="(\d{4}-\d{2}-\d{2})" id="([^"]+)"', html))
    counts = {}
    for cell, text in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html):
        number = re.match(r"(\d+) contribution", text)
        counts[cell] = int(number.group(1)) if number else 0
    return {date: counts.get(cell, 0) for date, cell in dates.items()}


def calendar(created_year, today):
    """Every contribution day since the account was created, as {date: count}."""
    days = {}
    for year in range(created_year, today.year + 1):
        year_days = from_graphql(year) or from_public_page(year)
        if year_days is None:
            return None
        days.update(year_days)
    return days


def streaks(days, today):
    """(current streak, longest streak, longest-streak end date)."""
    current = 0
    cursor = today
    # A day with no contributions yet doesn't break today's streak.
    if days.get(cursor.isoformat(), 0) == 0:
        cursor -= dt.timedelta(days=1)
    while days.get(cursor.isoformat(), 0) > 0:
        current += 1
        cursor -= dt.timedelta(days=1)

    longest = run = 0
    previous = None
    for date in sorted(days):
        day = dt.date.fromisoformat(date)
        if days[date] > 0:
            run = run + 1 if previous and (day - previous).days == 1 else 1
            longest = max(longest, run)
            previous = day
        else:
            previous = None
    return current, longest


def level(count, ceiling):
    if count <= 0:
        return 0
    return min(4, 1 + int(3 * count / max(ceiling, 1)))


def card(theme, days, today):
    t = kit.THEMES[theme]
    start = today - dt.timedelta(days=today.weekday() % 7 + (WEEKS - 1) * 7)
    window = {d: c for d, c in days.items() if dt.date.fromisoformat(d) >= start}
    ceiling = max(window.values() or [1])
    year_total = sum(window.values())
    current, longest = streaks(days, today)
    best_day = max(window.items(), key=lambda kv: kv[1], default=("", 0))

    width = MARGIN_X * 2 + WEEKS * STEP - GAP
    height = GRID_Y + 7 * STEP + 78
    svg = kit.open_card(width, height, theme, "Contributions", "last 12 months")

    labelled = set()
    for w in range(WEEKS):
        for d in range(7):
            date = start + dt.timedelta(days=w * 7 + d)
            if date > today:
                continue
            count = days.get(date.isoformat(), 0)
            x, y = MARGIN_X + w * STEP, GRID_Y + d * STEP
            if d == 0 and date.month not in labelled and date.day <= 7:
                labelled.add(date.month)
                svg += f'  <text x="{x}" y="{GRID_Y - 8}" class="muted">{MONTHS[date.month - 1]}</text>\n'
            svg += (
                f'  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" '
                f'fill="{t["heat"][level(count, ceiling)]}">'
                f'<title>{date.isoformat()}: {count}</title></rect>\n'
            )

    stats = [
        ("🔥 Current streak", f"{current} days"),
        ("🏆 Longest streak", f"{longest} days"),
        ("📅 Contributions", f"{year_total:,}"),
        ("⚡ Best day", f"{best_day[1]}"),
    ]
    y = GRID_Y + 7 * STEP + 40
    for i, (label, value) in enumerate(stats):
        x = MARGIN_X + i * ((width - MARGIN_X * 2) // len(stats))
        svg += (
            f'  <g class="row" style="animation-delay:{0.2 + i * 0.1:.2f}s">\n'
            f'    <text x="{x}" y="{y}" class="muted">{kit.esc(label)}</text>\n'
            f'    <text x="{x}" y="{y + 22}" class="big">{kit.esc(value)}</text>\n'
            f"  </g>\n"
        )
    return svg + "</svg>\n"


def main():
    user = gh.get(f"/users/{gh.USER}")
    if not user:
        sys.exit("GitHub API unreachable — contribution card left untouched")

    today = dt.date.fromisoformat(os.environ.get("TODAY") or dt.date.today().isoformat())
    days = calendar(int(user["created_at"][:4]), today)
    if not days:
        sys.exit("could not read the contribution calendar — card left untouched")

    os.makedirs(ASSETS, exist_ok=True)
    for theme in kit.THEMES:
        path = os.path.join(ASSETS, f"contrib-{theme}.svg")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(card(theme, days, today))
        print(f"wrote assets/contrib-{theme}.svg")


if __name__ == "__main__":
    main()
