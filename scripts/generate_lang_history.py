#!/usr/bin/env python3
"""Draw how my language mix changed over the years.

One stacked bar per year, split by the primary language of the repositories
started that year. Outputs: assets/lang-history-{dark,light}.svg
"""

import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gh  # noqa: E402
import svgkit as kit  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

WIDTH, HEIGHT = 737, 300
PLOT_TOP, PLOT_BOTTOM = 70, 210
BAR_W = 46


def by_year(repos):
    years = defaultdict(Counter)
    for repo in repos:
        if repo["language"]:
            years[int(repo["created_at"][:4])][repo["language"]] += 1
    return years


def card(theme, years):
    t = kit.THEMES[theme]
    order = sorted(years)
    if not order:
        return None
    totals = Counter()
    for counts in years.values():
        totals.update(counts)
    ranking = [lang for lang, _ in totals.most_common()]
    colors = {lang: kit.lang_color(lang, i) for i, lang in enumerate(ranking)}
    tallest = max(sum(c.values()) for c in years.values())
    span = PLOT_BOTTOM - PLOT_TOP
    gap = (WIDTH - 50) / len(order)

    svg = kit.open_card(WIDTH, HEIGHT, theme, "How my stack evolved",
                        "repositories started each year")
    svg += f'  <line x1="25" y1="{PLOT_BOTTOM}" x2="{WIDTH - 25}" y2="{PLOT_BOTTOM}" stroke="{t["border"]}"/>\n'

    for i, year in enumerate(order):
        total = sum(years[year].values())
        x = 25 + gap * i + (gap - BAR_W) / 2
        y = PLOT_BOTTOM
        for lang, count in sorted(years[year].items(), key=lambda kv: -kv[1]):
            h = span * count / tallest
            y -= h
            svg += (
                f'  <rect x="{x:.1f}" y="{y:.1f}" width="{BAR_W}" height="{h:.1f}" '
                f'fill="{colors[lang]}"><title>{year} · {lang}: {count}</title></rect>\n'
            )
        svg += (
            f'  <text x="{x + BAR_W / 2:.1f}" y="{y - 8:.1f}" class="value" text-anchor="middle">{total}</text>\n'
            f'  <text x="{x + BAR_W / 2:.1f}" y="{PLOT_BOTTOM + 20:.1f}" class="muted" text-anchor="middle">{year}</text>\n'
        )

    x, y = 25, PLOT_BOTTOM + 55
    for i, lang in enumerate(ranking[:6]):
        svg += (
            f'  <g class="row" style="animation-delay:{0.2 + i * 0.08:.2f}s">\n'
            f'    <rect x="{x}" y="{y - 10}" width="10" height="10" rx="2" fill="{colors[lang]}"/>\n'
            f'    <text x="{x + 16}" y="{y}" class="label">{kit.esc(lang)}</text>\n'
            f"  </g>\n"
        )
        x += 24 + len(lang) * 8
    return svg + "</svg>\n"


def main():
    repos = gh.own_repos()
    if not repos:
        sys.exit("GitHub API unreachable — language history left untouched")

    os.makedirs(ASSETS, exist_ok=True)
    for theme in kit.THEMES:
        svg = card(theme, by_year(repos))
        if not svg:
            return
        with open(os.path.join(ASSETS, f"lang-history-{theme}.svg"), "w", encoding="utf-8") as fh:
            fh.write(svg)
        print(f"wrote assets/lang-history-{theme}.svg")


if __name__ == "__main__":
    main()
