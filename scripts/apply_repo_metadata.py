#!/usr/bin/env python3
"""Push the curated descriptions and topics in repo_metadata.json to GitHub.

Dry run by default — nothing is written until you pass --apply.

    export GH_TOKEN=<personal access token with 'repo' scope>
    python scripts/apply_repo_metadata.py            # show what would change
    python scripts/apply_repo_metadata.py --apply    # actually write it
"""

import json
import os
import sys
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gh  # noqa: E402

META = os.path.join(os.path.dirname(os.path.abspath(__file__)), "repo_metadata.json")
APPLY = "--apply" in sys.argv


def main():
    if APPLY and not (os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")):
        sys.exit("GH_TOKEN is required for --apply (needs the 'repo' scope)")

    with open(META, encoding="utf-8") as fh:
        wanted = json.load(fh)

    changed = skipped = 0
    for name, meta in wanted.items():
        repo = gh.get(f"/repos/{gh.USER}/{name}")
        if repo is None:
            print(f"?  {name}: not reachable, skipped")
            continue

        needs_desc = (repo.get("description") or "").strip() != meta["description"]
        current_topics = set(repo.get("topics") or [])
        needs_topics = not set(meta["topics"]).issubset(current_topics)

        if not (needs_desc or needs_topics):
            skipped += 1
            continue

        parts = []
        if needs_desc:
            parts.append(f"description={meta['description'][:60]}...")
        if needs_topics:
            parts.append(f"topics={'+'.join(sorted(set(meta['topics']) - current_topics))}")
        print(f"{'→' if APPLY else '·'}  {name}: {'; '.join(parts)}")
        changed += 1

        if not APPLY:
            continue
        try:
            if needs_desc:
                gh.request(f"/repos/{gh.USER}/{name}", "PATCH", {"description": meta["description"]})
            if needs_topics:
                gh.request(
                    f"/repos/{gh.USER}/{name}/topics",
                    "PUT",
                    {"names": sorted(current_topics | set(meta["topics"]))},
                )
        except urllib.error.HTTPError as err:
            print(f"   ! failed ({err.code}): {err.reason}")

    verb = "updated" if APPLY else "would be updated"
    print(f"\n{changed} repositories {verb}, {skipped} already fine.")
    if not APPLY and changed:
        print("Re-run with --apply to write the changes.")


if __name__ == "__main__":
    main()
