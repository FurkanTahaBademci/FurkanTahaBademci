#!/usr/bin/env python3
"""Fill in the GitHub profile fields that are still empty (website, location, bio).

Dry run by default; needs a token with the 'user' scope for --apply.

    export GH_TOKEN=<token with 'user' scope>
    python scripts/setup_profile.py --apply
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gh  # noqa: E402

APPLY = "--apply" in sys.argv

PROFILE = {
    "blog": "https://furkantahabademci.github.io",
    "location": "Türkiye",
    "bio": "Artificial intelligence researcher - Computer vision - Deep learning",
}


def main():
    if APPLY and not (os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")):
        sys.exit("GH_TOKEN with the 'user' scope is required for --apply")

    current = gh.get(f"/users/{gh.USER}") or {}
    diff = {k: v for k, v in PROFILE.items() if (current.get(k) or "").strip() != v}

    if not diff:
        print("Profile already matches — nothing to do.")
        return

    for key, value in diff.items():
        print(f"{'→' if APPLY else '·'}  {key}: {current.get(key) or '(empty)'!r} -> {value!r}")

    if APPLY:
        gh.request("/user", "PATCH", diff)
        print("\nProfile updated.")
    else:
        print("\nRe-run with --apply to write the changes.")


if __name__ == "__main__":
    main()
