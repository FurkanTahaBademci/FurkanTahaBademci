#!/usr/bin/env python3
"""Refresh the auto-generated blocks of the profile READMEs (English + Turkish).

Blocks are delimited by HTML comment markers, so the hand-written parts of the
files are never touched:

    <!-- NOW:START -->            what I pushed to most recently
    <!-- LATEST-REPOS:START -->   the five most recently pushed repositories
    <!-- ACTIVITY:START -->       what I did on GitHub most recently
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
        "events": {
            "push": "Pushed {n} commit{s} to",
            "create_repo": "Created",
            "create_branch": "Opened a new branch in",
            "release": "Published a release of",
            "star": "Starred",
            "fork": "Forked",
            "pr": "Opened a pull request on",
            "issue": "Opened an issue on",
        },
    },
    "README.tr.md": {
        "now": "🔨 Şu an üzerinde çalıştığım proje:",
        "head": ["Depo", "Açıklama", "Dil", "⭐", "Son push"],
        "note": "Her gün GitHub Actions tarafından otomatik üretilir — elle düzenlemeye gerek yok.",
        "nodesc": "—",
        "events": {
            "push": "{n} commit gönderdi:",
            "create_repo": "Yeni depo açtı:",
            "create_branch": "Yeni dal açtı:",
            "release": "Sürüm yayınladı:",
            "star": "Yıldızladı:",
            "fork": "Fork'ladı:",
            "pr": "Pull request açtı:",
            "issue": "Issue açtı:",
        },
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


class DefaultFields(dict):
    """Lets a translation ignore fields it does not use (e.g. the plural 's')."""

    def __missing__(self, key):
        return ""


ICONS = {"push": "⬆️", "create_repo": "✨", "create_branch": "🌱", "release": "🚀",
         "star": "⭐", "fork": "🍴", "pr": "🔀", "issue": "🐛"}


def classify(event):
    """Map a raw GitHub event onto one of the phrases we know how to print."""
    kind = event["type"]
    payload = event.get("payload", {})
    if kind == "PushEvent":
        size = payload.get("size", 1)
        return "push", {"n": size, "s": "" if size == 1 else "s"}
    if kind == "CreateEvent":
        ref = payload.get("ref_type")
        if ref == "repository":
            return "create_repo", {}
        if ref == "branch":
            return "create_branch", {}
    if kind == "ReleaseEvent":
        return "release", {}
    if kind == "WatchEvent":
        return "star", {}
    if kind == "ForkEvent":
        return "fork", {}
    if kind == "PullRequestEvent" and payload.get("action") == "opened":
        return "pr", {}
    if kind == "IssuesEvent" and payload.get("action") == "opened":
        return "issue", {}
    return None, {}


def short(repo):
    """Own repositories read better without the owner prefix; others keep it."""
    owner, name = repo.split("/", 1)
    return name if owner == gh.USER else repo


def collapse(events):
    """Merge events of the same kind on the same repository and day.

    Four separate one-commit pushes to the same repo on the same afternoon
    read as noise; "Pushed 4 commits" is what actually happened.
    """
    merged = {}
    for event in events:
        kind, fields = classify(event)
        if not kind:
            continue
        repo = event["repo"]["name"]
        # Skip the profile repo's own automated refresh commits.
        if kind == "push" and repo == f"{gh.USER}/{gh.USER}":
            continue
        key = (kind, repo, event["created_at"][:10])
        if key in merged:
            merged[key]["n"] = merged[key].get("n", 0) + fields.get("n", 0)
        else:
            merged[key] = dict(fields)
    return merged


def render_activity(events, s, limit=5):
    lines = []
    for (kind, repo, date), fields in list(collapse(events).items())[:limit]:
        if "n" in fields:
            fields["s"] = "" if fields["n"] == 1 else "s"
        phrase = s["events"][kind].format_map(DefaultFields(fields))
        lines.append(
            f"- {ICONS[kind]} {phrase} [{short(repo)}](https://github.com/{repo}) "
            f"<sub>{date}</sub>"
        )
    return "\n".join(lines) if lines else f"<sub>{s['note']}</sub>"


def main():
    repos = [r for r in gh.own_repos() if r["name"] != gh.USER]
    events = gh.get(f"/users/{gh.USER}/events/public?per_page=100", []) or []
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
        blocks = (
            ("NOW", render_now(repos, s)),
            ("LATEST-REPOS", render_table(repos, s)),
            ("ACTIVITY", render_activity(events, s)),
        )
        for name, body in blocks:
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
