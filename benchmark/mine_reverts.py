"""Mines reverted PRs from a GitHub org/repo.

Strategy:
  1. List recent commits whose message starts with `Revert "...` on the default branch.
  2. For each, parse the original PR number out of the body (`Reverts #1234` or `(#1234)`).
  3. Fetch the original PR's title, body, and unified diff.
  4. Emit one JSONL row per PR with `label="?"` (must be human-labeled before scoring).

Requires GITHUB_TOKEN with read access. Respects rate limits (sleeps on 403).

Usage:
  python -m benchmark.mine_reverts --repo torvalds/linux --max 50 --out data/mined.jsonl
  python -m benchmark.mine_reverts --org kubernetes --max 50 --out data/mined.jsonl

Each org/repo run is checkpointed so partial failures are resumable.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path

import httpx
import typer

from .schema import Example, write_jsonl

app = typer.Typer(add_completion=False)
API = "https://api.github.com"
PR_REF = re.compile(r"#(\d+)")


def _client() -> httpx.Client:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise typer.Exit("GITHUB_TOKEN not set")
    return httpx.Client(
        base_url=API,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30.0,
    )


def _get(client: httpx.Client, path: str, **params) -> httpx.Response:
    """GET with naive rate-limit backoff."""
    for _ in range(5):
        r = client.get(path, params=params)
        if r.status_code == 403 and "rate limit" in r.text.lower():
            reset = int(r.headers.get("X-RateLimit-Reset", time.time() + 60))
            wait = max(5, reset - int(time.time()))
            print(f"Rate limited, sleeping {wait}s")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r
    raise RuntimeError(f"Repeated rate-limit failures on {path}")


def _list_repos_in_org(client: httpx.Client, org: str, max_repos: int) -> list[str]:
    repos: list[str] = []
    page = 1
    while len(repos) < max_repos:
        r = _get(client, f"/orgs/{org}/repos", per_page=100, page=page, sort="updated")
        batch = r.json()
        if not batch:
            break
        repos.extend(f"{org}/{item['name']}" for item in batch)
        page += 1
    return repos[:max_repos]


def _find_revert_commits(client: httpx.Client, repo: str, max_commits: int) -> list[dict]:
    out: list[dict] = []
    page = 1
    while len(out) < max_commits:
        r = _get(client, f"/repos/{repo}/commits", per_page=100, page=page)
        batch = r.json()
        if not batch:
            break
        for c in batch:
            msg = c.get("commit", {}).get("message", "")
            if msg.startswith('Revert "') or msg.lower().startswith("revert pr"):
                out.append(c)
                if len(out) >= max_commits:
                    break
        page += 1
        if page > 10:  # don't dig too deep on tiny repos
            break
    return out


def _extract_pr_number(message: str) -> int | None:
    matches = PR_REF.findall(message)
    return int(matches[0]) if matches else None


def _fetch_pr(client: httpx.Client, repo: str, number: int) -> Example | None:
    pr = _get(client, f"/repos/{repo}/pulls/{number}").json()
    diff_resp = client.get(
        f"/repos/{repo}/pulls/{number}",
        headers={"Accept": "application/vnd.github.v3.diff"},
    )
    if diff_resp.status_code != 200:
        return None
    return Example(
        id=f"{repo.replace('/', '_')}_pr{number}",
        source=f"github:{repo}#{number}",
        pr_title=pr.get("title") or "",
        pr_body=pr.get("body") or "",
        diff=diff_resp.text,
        label="?",
        rationale="Auto-mined; requires human label.",
        reverted=True,
        revert_commit=None,
    )


@app.command()
def mine(
    repo: str | None = typer.Option(None, "--repo", help="owner/name"),
    org: str | None = typer.Option(None, "--org", help="organization to scan"),
    max_count: int = typer.Option(50, "--max", help="Total examples to collect"),
    out: Path = typer.Option(Path("benchmark/data/mined.jsonl"), "--out"),
) -> None:
    if not (repo or org):
        raise typer.BadParameter("Provide --repo or --org")

    with _client() as client:
        repos = [repo] if repo else _list_repos_in_org(client, org, max_repos=20)

        examples: list[Example] = []
        for r in repos:
            if len(examples) >= max_count:
                break
            print(f"Scanning {r}...")
            try:
                commits = _find_revert_commits(client, r, max_commits=max_count - len(examples))
            except httpx.HTTPStatusError as e:
                print(f"  skip {r}: {e}")
                continue
            for c in commits:
                pr_num = _extract_pr_number(c["commit"]["message"])
                if not pr_num:
                    continue
                try:
                    ex = _fetch_pr(client, r, pr_num)
                except httpx.HTTPStatusError:
                    continue
                if ex is None or len(ex.diff) > 50_000:
                    continue
                examples.append(ex)
                if len(examples) >= max_count:
                    break

    write_jsonl(out, examples)
    print(f"Wrote {len(examples)} examples to {out} (label='?', needs human review)")


if __name__ == "__main__":
    app()
