#!/usr/bin/env python3
"""Render the profile stat cards as local SVG files.

Everything the README shows is produced here from the GitHub API, so the
profile never depends on a third-party card service being up.
Outputs (light + dark variants): assets/stats-*.svg, assets/langs-*.svg
"""

import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gh  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
TOP_LANGS = 8

THEMES = {
    "dark": {
        "bg": "#0d1117", "border": "#30363d", "title": "#58a6ff",
        "text": "#c9d1d9", "muted": "#8b949e", "value": "#f0f6fc", "track": "#21262d",
    },
    "light": {
        "bg": "#ffffff", "border": "#d0d7de", "title": "#0969da",
        "text": "#1f2328", "muted": "#59636e", "value": "#1f2328", "track": "#eaeef2",
    },
}

# Colours follow GitHub's linguist palette for the languages actually in use.
LANG_COLORS = {
    "Python": "#3572A5", "Dart": "#00B4AB", "Jupyter Notebook": "#DA5B0B",
    "C": "#555555", "C++": "#f34b7d", "CSS": "#663399", "HTML": "#e34c26",
    "JavaScript": "#f1e05a", "ActionScript": "#882B0F", "Shell": "#89e051",
    "Ruby": "#701516", "Java": "#b07219", "Kotlin": "#A97BFF", "Swift": "#F05138",
    "CMake": "#DA3434", "Batchfile": "#C1F12E", "TypeScript": "#3178c6",
}
FALLBACK_COLORS = ["#58a6ff", "#3fb950", "#d29922", "#f85149", "#a371f7", "#db61a2"]

FONT = "-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif"


def esc(text):
    return (
        str(text).replace("&", "&amp;").replace("<", "&lt;")
        .replace(">", "&gt;").replace('"', "&quot;")
    )


def header(width, height, theme, title):
    t = THEMES[theme]
    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{esc(title)}">
  <style>
    .title {{ font: 600 18px {FONT}; fill: {t['title']}; }}
    .label {{ font: 400 14px {FONT}; fill: {t['text']}; }}
    .value {{ font: 700 14px {FONT}; fill: {t['value']}; }}
    .muted {{ font: 400 11px {FONT}; fill: {t['muted']}; }}
    .row {{ opacity: 0; animation: fade 0.5s ease-in-out forwards; }}
    @keyframes fade {{ from {{ opacity: 0; transform: translateX(-6px); }} to {{ opacity: 1; transform: translateX(0); }} }}
  </style>
  <rect x="0.5" y="0.5" rx="10" width="{width - 1}" height="{height - 1}" fill="{t['bg']}" stroke="{t['border']}"/>
  <text x="25" y="35" class="title">{esc(title)}</text>
"""


def stats_card(theme, user, repos, commits):
    stars = sum(r["stargazers_count"] for r in repos)
    forks = sum(r["forks_count"] for r in repos)
    rows = [
        ("⭐  Total Stars Earned", stars),
        ("📦  Public Repositories", user.get("public_repos", len(repos))),
        ("🔱  Forks of My Repos", forks),
        ("👥  Followers", user.get("followers", 0)),
    ]
    if commits is not None:
        rows.insert(1, ("🧬  Commits (all time)", commits))

    height = 90 + len(rows) * 30
    svg = header(495, height, theme, f"{user.get('name') or gh.USER} · GitHub Stats")
    y = 68
    for i, (label, value) in enumerate(rows):
        delay = 0.15 + i * 0.1
        svg += (
            f'  <g class="row" style="animation-delay:{delay:.2f}s">\n'
            f'    <text x="25" y="{y}" class="label">{esc(label)}</text>\n'
            f'    <text x="465" y="{y}" class="value" text-anchor="end">{value:,}</text>\n'
            f"  </g>\n"
        )
        y += 30
    svg += f'  <text x="25" y="{height - 18}" class="muted">Generated automatically from the GitHub API</text>\n</svg>\n'
    return svg


def language_usage(repos):
    """Share of repositories per primary language.

    Deliberately repo-count based rather than byte based: Flutter/Android
    projects ship thousands of generated lines that would otherwise drown
    out every hand-written Python project.
    """
    return Counter(r["language"] for r in repos if r["language"])


def langs_card(theme, totals):
    t = THEMES[theme]
    top = totals.most_common(TOP_LANGS)
    total = sum(v for _, v in totals.items()) or 1
    width, bar_w, bar_x, bar_y = 495, 445, 25, 55

    svg = header(width, 100 + ((len(top) + 1) // 2) * 26, theme, "Languages I Build With")
    svg += f'  <rect x="{bar_x}" y="{bar_y}" rx="5" width="{bar_w}" height="10" fill="{t["track"]}"/>\n'

    offset, segments = 0.0, []
    for i, (lang, count) in enumerate(top):
        color = LANG_COLORS.get(lang, FALLBACK_COLORS[i % len(FALLBACK_COLORS)])
        share = count / total
        seg_w = max(share * bar_w, 2)
        segments.append((lang, count, share, color))
        svg += (
            f'  <rect x="{bar_x + offset:.1f}" y="{bar_y}" width="{seg_w:.1f}" height="10" '
            f'fill="{color}"{" rx=\"5\"" if i == 0 else ""}/>\n'
        )
        offset += share * bar_w

    y = bar_y + 40
    for i, (lang, count, share, color) in enumerate(segments):
        x = 25 if i % 2 == 0 else 260
        svg += (
            f'  <g class="row" style="animation-delay:{0.2 + i * 0.08:.2f}s">\n'
            f'    <circle cx="{x + 5}" cy="{y - 4}" r="5" fill="{color}"/>\n'
            f'    <text x="{x + 18}" y="{y}" class="label">{esc(lang)}</text>\n'
            f'    <text x="{x + 205}" y="{y}" class="value" text-anchor="end">{count} repo · {share * 100:.0f}%</text>\n'
            f"  </g>\n"
        )
        if i % 2 == 1:
            y += 26
    return svg + "</svg>\n"


def main():
    user = gh.get(f"/users/{gh.USER}")
    if not user:
        sys.exit("GitHub API unreachable — cards left untouched")
    repos = gh.own_repos()
    search = gh.get(f"/search/commits?q=author:{gh.USER}&per_page=1")
    commits = search.get("total_count") if isinstance(search, dict) else None
    totals = language_usage(repos)

    os.makedirs(ASSETS, exist_ok=True)
    for theme in THEMES:
        for name, svg in (
            (f"stats-{theme}.svg", stats_card(theme, user, repos, commits)),
            (f"langs-{theme}.svg", langs_card(theme, totals)),
        ):
            with open(os.path.join(ASSETS, name), "w", encoding="utf-8") as fh:
                fh.write(svg)
            print(f"wrote assets/{name}")


if __name__ == "__main__":
    main()
