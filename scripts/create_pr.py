#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request


def run_capture(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()


def get_owner_repo() -> str:
    origin = run_capture(["git", "remote", "get-url", "origin"])  # e.g. https://github.com/owner/repo(.git)
    owner_repo = re.sub(r"^https?://[^/]+/", "", origin)
    if owner_repo.endswith(".git"):
        owner_repo = owner_repo[:-4]
    return owner_repo


def get_current_branch() -> str:
    return run_capture(["git", "rev-parse", "--abbrev-ref", "HEAD"])  # e.g. feature-branch


def get_token() -> str | None:
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        return token
    try:
        remotes = run_capture(["git", "remote", "-v"])  # may contain x-access-token
        m = re.search(r"x-access-token:([^@]+)@github\\.com", remotes)
        if m:
            return m.group(1)
    except Exception:
        pass
    return None


def create_pr(owner_repo: str, head: str, base: str = "master") -> str:
    token = get_token()
    if not token:
        print("GitHub token not found. Set GITHUB_TOKEN or GH_TOKEN.")
        sys.exit(1)

    url = f"https://api.github.com/repos/{owner_repo}/pulls"
    payload = {
        "title": "Create new pull request to master",
        "head": head,
        "base": base,
        "body": f"Automated PR from branch {head} to {base}.",
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            out = json.load(resp)
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode("utf-8", "ignore"))
        except Exception:
            err = {"message": str(e)}
        print(f"Failed to create PR: {err.get('message', err)}")
        if "errors" in err:
            print(json.dumps(err["errors"], indent=2))
        sys.exit(1)

    url = out.get("html_url")
    if not url:
        print(json.dumps(out, indent=2))
        sys.exit(1)
    return url


def main() -> None:
    owner_repo = get_owner_repo()
    head = get_current_branch()
    pr_url = create_pr(owner_repo=owner_repo, head=head, base="master")
    print(pr_url)


if __name__ == "__main__":
    main()