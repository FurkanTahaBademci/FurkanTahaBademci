#!/usr/bin/env python3
"""Refresh the auto-generated blocks of the profile READMEs (English + Turkish).

Blocks are delimited by HTML comment markers, so the hand-written parts of the
files are never touched:

    <!-- NOW:START -->            what I pushed to most recently
    <!-- LATEST-REPOS:START -->   the five most recently pushed repositories
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gh  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COUNT = int(os.environ.get("REPO_COUNT", "5"))

STRINGS = {
    "README.md": {
        "now": "🔨 Currently working on",
        "head": ["Repository", "Description", "Language", "⭐", "Last push"],
        "note": "Auto-generated daily by a GitHub Action — no manual edits needed.",
        "nodesc": "—",
    },
    "README.tr.md": {
        "now": "🔨 Şu an üzerinde çalıştığım proje:",
        "head": ["Depo", "Açıklama", "Dil", "⭐", "Son push"],
        "note": "Her gün GitHub Actions tarafından otomatik üretilir — elle düzenlemeye gerek yok.",
        "nodesc": "—",
    },
}


def block(name, body):
    return f"<!-- {name}:START -->\n{body}\n<!-- {name}:END -->"


def render_now(repos, s):
    top = repos[0]
    desc = f" — {top['description']}" if top.get("description") else ""
    return (
        f"{s['now']} **[{top['name']}]({top['html_url']})**{desc} "
        f"<sub>(last push {top['pushed_at'][:10]})</sub>"
    )


def render_table(repos, s):
    rows = ["| " + " | ".join(s["head"]) + " |", "| --- | --- | --- | --- | --- |"]
    for r in repos[:COUNT]:
        desc = (r["description"] or s["nodesc"]).replace("|", "\\|")
        rows.append(
            f"| [{r['name']}]({r['html_url']}) | {desc} | {r['language'] or s['nodesc']} "
            f"| {r['stargazers_count']} | {r['pushed_at'][:10]} |"
        )
    return "\n".join(rows) + f"\n\n<sub>{s['note']}</sub>"


def main():
    repos = [r for r in gh.own_repos() if r["name"] != gh.USER]
    if not repos:
        sys.exit("GitHub API unreachable — READMEs left untouched")

    touched = []
    for filename, s in STRINGS.items():
        path = os.path.join(ROOT, filename)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            original = fh.read()

        updated = original
        for name, body in (("NOW", render_now(repos, s)), ("LATEST-REPOS", render_table(repos, s))):
            if f"<!-- {name}:START -->" not in updated:
                continue
            updated = re.sub(
                re.escape(f"<!-- {name}:START -->") + r".*?" + re.escape(f"<!-- {name}:END -->"),
                lambda _, b=block(name, body): b,
                updated,
                flags=re.DOTALL,
            )

        if updated != original:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(updated)
            touched.append(filename)

    print(f"updated: {', '.join(touched)}" if touched else "everything already up to date")


if __name__ == "__main__":
    main()
