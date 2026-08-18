#!/usr/bin/env python3
"""Weekly check for repositories missing a description, topics or a licence.

Opens (or refreshes) a single issue on the profile repository listing what is
missing, and closes it again once everything is in order. Dry run by default.

    python scripts/check_repo_hygiene.py            # print the report
    GH_TOKEN=... python scripts/check_repo_hygiene.py --apply
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gh  # noqa: E402

APPLY = "--apply" in sys.argv
TITLE = "🧹 Repository hygiene report"
MARKER = "<!-- hygiene-bot -->"
REPO = f"/repos/{gh.USER}/{gh.USER}"


def audit(repos):
    findings = []
    for repo in sorted(repos, key=lambda r: r["name"].lower()):
        missing = []
        if not (repo.get("description") or "").strip():
            missing.append("description")
        if not repo.get("topics"):
            missing.append("topics")
        if not repo.get("license"):
            missing.append("licence")
        if missing:
            findings.append((repo, missing))
    return findings


def report(findings, total):
    lines = [
        MARKER,
        f"{len(findings)} of {total} repositories are missing metadata that GitHub search "
        "and the profile cards rely on.",
        "",
        "| Repository | Missing |",
        "| --- | --- |",
    ]
    for repo, missing in findings:
        lines.append(f"| [{repo['name']}]({repo['html_url']}) | {', '.join(missing)} |")
    lines += [
        "",
        "Descriptions and topics for known repositories live in "
        f"[`scripts/repo_metadata.json`](https://github.com/{gh.USER}/{gh.USER}/blob/main/"
        "scripts/repo_metadata.json) — add the new ones there and run "
        "`python scripts/apply_repo_metadata.py --apply`.",
        "",
        "<sub>Opened automatically by the weekly hygiene workflow.</sub>",
    ]
    return "\n".join(lines)


def existing_issue():
    issues = gh.get(f"{REPO}/issues?state=open&per_page=100", []) or []
    return next((i for i in issues if i["title"] == TITLE and "pull_request" not in i), None)


def main():
    repos = [r for r in gh.own_repos() if r["name"] != gh.USER]
    if not repos:
        sys.exit("GitHub API unreachable — hygiene check skipped")

    findings = audit(repos)
    issue = existing_issue()

    if not findings:
        print("Every repository has a description, topics and a licence. 🎉")
        if APPLY and issue:
            gh.request(f"{REPO}/issues/{issue['number']}", "PATCH", {"state": "closed"})
            print(f"closed issue #{issue['number']}")
        return

    body = report(findings, len(repos))
    print(body)

    if not APPLY:
        print("\nRe-run with --apply to open or update the tracking issue.")
        return

    if issue:
        gh.request(f"{REPO}/issues/{issue['number']}", "PATCH", {"body": body})
        print(f"\nupdated issue #{issue['number']}")
    else:
        created = gh.request(f"{REPO}/issues", "POST", {"title": TITLE, "body": body})
        print(f"\nopened issue #{created['number']}")


if __name__ == "__main__":
    main()
