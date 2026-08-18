#!/usr/bin/env python3
"""Draw the animated typing header shown at the top of the README.

Pure CSS inside the SVG, so it animates wherever GitHub renders it and needs
no third-party typing service. Outputs: assets/typing-{dark,light}.svg
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgkit as kit  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

PHRASES = [
    "Artificial Intelligence Researcher",
    "Computer Vision & Deep Learning",
    "Flutter Developer · Hardware Tinkerer",
]
WIDTH, HEIGHT = 737, 70
FONT_SIZE = 24
CHAR_W = FONT_SIZE * 0.56  # rough advance width for the fallback sans stack
TYPE_S, HOLD_S = 1.6, 2.4  # seconds spent typing / holding each phrase


def card(theme):
    t = kit.THEMES[theme]
    slot = TYPE_S + HOLD_S
    cycle = slot * len(PHRASES)
    css, defs, body = [], [], []

    for i, phrase in enumerate(PHRASES):
        width = len(phrase) * CHAR_W
        start = (i * slot) / cycle * 100
        typed = (i * slot + TYPE_S) / cycle * 100
        end = ((i + 1) * slot) / cycle * 100

        # The reveal is a clip rectangle whose width grows one character at a
        # time — animating the geometry property keeps it identical across
        # renderers, unlike clip-path shapes on SVG text.
        defs.append(
            f'    <clipPath id="clip{i}"><rect class="reveal r{i}" x="25" y="0" '
            f'height="{HEIGHT}" width="0"/></clipPath>\n'
        )
        css.append(
            f"    @keyframes r{i} {{"
            f" 0%,{start:.2f}% {{ width: 0; }}"
            f" {typed:.2f}%,{end - 0.01:.2f}% {{ width: {width:.0f}px; }}"
            f" {end:.2f}%,100% {{ width: 0; }} }}\n"
            f"    @keyframes k{i} {{"
            f" 0%,{start:.2f}% {{ opacity: 0; transform: translateX(0); }}"
            f" {start + 0.01:.2f}% {{ opacity: 1; transform: translateX(0); }}"
            f" {typed:.2f}%,{end - 0.01:.2f}% {{ opacity: 1; transform: translateX({width:.0f}px); }}"
            f" {end:.2f}%,100% {{ opacity: 0; transform: translateX({width:.0f}px); }} }}\n"
            f"    .r{i} {{ animation: r{i} {cycle:.1f}s steps({len(phrase)}, end) infinite; }}\n"
            f"    .c{i} {{ animation: k{i} {cycle:.1f}s steps({len(phrase)}, end) infinite,"
            f" blink 1s step-end infinite; }}\n"
        )
        body.append(
            f'  <text x="25" y="45" class="phrase" clip-path="url(#clip{i})">{kit.esc(phrase)}</text>\n'
            f'  <rect x="27" y="26" width="2" height="24" class="cursor c{i}" fill="{t["title"]}"/>\n'
        )

    return (
        f'<svg width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" fill="none" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{kit.esc(" / ".join(PHRASES))}">\n'
        "  <style>\n"
        f"    .phrase {{ font: 600 {FONT_SIZE}px {kit.FONT}; fill: {t['title']}; }}\n"
        "    .cursor { opacity: 0; }\n"
        "    @keyframes blink { 0%,50% { fill-opacity: 1; } 51%,100% { fill-opacity: 0; } }\n"
        + "".join(css)
        + "  </style>\n  <defs>\n"
        + "".join(defs)
        + "  </defs>\n"
        + "".join(body)
        + "</svg>\n"
    )


def main():
    os.makedirs(ASSETS, exist_ok=True)
    for theme in kit.THEMES:
        with open(os.path.join(ASSETS, f"typing-{theme}.svg"), "w", encoding="utf-8") as fh:
            fh.write(card(theme))
        print(f"wrote assets/typing-{theme}.svg")


if __name__ == "__main__":
    main()
