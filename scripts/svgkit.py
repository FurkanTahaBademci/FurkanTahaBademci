"""Shared drawing helpers for the profile cards."""

THEMES = {
    "dark": {
        "bg": "#0d1117", "border": "#30363d", "title": "#58a6ff",
        "text": "#c9d1d9", "muted": "#8b949e", "value": "#f0f6fc", "track": "#21262d",
        "heat": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
    },
    "light": {
        "bg": "#ffffff", "border": "#d0d7de", "title": "#0969da",
        "text": "#1f2328", "muted": "#59636e", "value": "#1f2328", "track": "#eaeef2",
        "heat": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
    },
}

FONT = "-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif"

# GitHub's linguist colours for the languages that actually show up here.
LANG_COLORS = {
    "Python": "#3572A5", "Dart": "#00B4AB", "Jupyter Notebook": "#DA5B0B",
    "C": "#555555", "C++": "#f34b7d", "CSS": "#663399", "HTML": "#e34c26",
    "JavaScript": "#f1e05a", "ActionScript": "#882B0F", "Shell": "#89e051",
    "Java": "#b07219", "Kotlin": "#A97BFF", "Swift": "#F05138", "TypeScript": "#3178c6",
    "CMake": "#DA3434", "Batchfile": "#C1F12E", "Ruby": "#701516",
}
FALLBACK_COLORS = ["#58a6ff", "#3fb950", "#d29922", "#f85149", "#a371f7", "#db61a2"]


def lang_color(language, index=0):
    return LANG_COLORS.get(language, FALLBACK_COLORS[index % len(FALLBACK_COLORS)])


def esc(text):
    return (
        str(text).replace("&", "&amp;").replace("<", "&lt;")
        .replace(">", "&gt;").replace('"', "&quot;")
    )


def open_card(width, height, theme, title, subtitle=None, extra_css=""):
    t = THEMES[theme]
    svg = f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{esc(title)}">
  <style>
    .title {{ font: 600 18px {FONT}; fill: {t['title']}; }}
    .label {{ font: 400 14px {FONT}; fill: {t['text']}; }}
    .value {{ font: 700 14px {FONT}; fill: {t['value']}; }}
    .big {{ font: 700 22px {FONT}; fill: {t['value']}; }}
    .muted {{ font: 400 11px {FONT}; fill: {t['muted']}; }}
    .row {{ opacity: 0; animation: fade 0.5s ease-in-out forwards; }}
    @keyframes fade {{ from {{ opacity: 0; transform: translateX(-6px); }} to {{ opacity: 1; transform: translateX(0); }} }}
{extra_css}  </style>
  <rect x="0.5" y="0.5" rx="10" width="{width - 1}" height="{height - 1}" fill="{t['bg']}" stroke="{t['border']}"/>
  <text x="25" y="35" class="title">{esc(title)}</text>
"""
    if subtitle:
        svg += f'  <text x="{width - 25}" y="35" class="muted" text-anchor="end">{esc(subtitle)}</text>\n'
    return svg
