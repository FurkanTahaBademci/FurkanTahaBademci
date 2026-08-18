"""Tiny GitHub API helper shared by the README automation scripts."""

import json
import os
import urllib.error
import urllib.request

USER = os.environ.get("GH_USER", "FurkanTahaBademci")
API = "https://api.github.com"


def request(path, method="GET", payload=None, accept="application/vnd.github+json"):
    url = path if path.startswith("http") else API + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", accept)
    req.add_header("User-Agent", USER)
    if data:
        req.add_header("Content-Type", "application/json")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read()
        return json.loads(body) if body else {}


def get(path, default=None):
    """GET that never raises — returns `default` on any failure."""
    try:
        return request(path)
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError):
        return default


def own_repos():
    """Non-fork, non-archived repositories owned by the user, newest push first."""
    repos = get(f"/users/{USER}/repos?per_page=100&sort=pushed", []) or []
    own = [r for r in repos if not r["fork"] and not r["archived"]]
    return sorted(own, key=lambda r: r["pushed_at"], reverse=True)
