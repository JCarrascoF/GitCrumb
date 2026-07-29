"""Parseo de la ejecución por terminal — subprocess → git log."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from gitrack.models import Commit


def _parse_log(output: str) -> list[Commit]:
    """Parse pipe-delimited git log output into Commit objects."""
    commits: list[Commit] = []
    for line in output.strip().splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            commits.append(Commit(
                short_hash=parts[0].strip(),
                date=parts[1].strip(),
                message=parts[2].strip(),
            ))
    return commits


def _git_log(repo_root: Path, author_pattern: str, start_date: str, end_date: str,
             merges_flag: str) -> list[Commit]:
    """Run a single git log query and return parsed commits."""
    cmd = [
        "git", "log", merges_flag, f"--author={author_pattern}",
        f"--since={start_date}", f"--until={end_date}T23:59:59",
        "--format=%h|%ad|%s", "--date=format:%Y-%m-%d",
    ]
    result = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True, timeout=30)
    return _parse_log(result.stdout) if result.returncode == 0 else []


def extract_commits(repo_root: Path, authors: list[str], start_date: str, end_date: str,
                    exclude_merges: bool = False, debug: bool = False) -> tuple[list[Commit], int, set[str]]:
    """Return (commits, merge_count, merge_hashes) for the given repo and date range.

    Runs one query per author pattern to avoid git's poor OR regex support.
    Deduplicates by commit hash. When *exclude_merges* is True, only non-merge commits are returned."""
    all_commits: dict[str, Commit] = {}   # dedup by hash, preserves first occurrence
    merge_hashes: set[str] = set()

    for author in authors:
        for flag, is_merge in (("--no-merges", False), ("--merges", True)):
            batch = _git_log(repo_root, author, start_date, end_date, flag)
            new_count = 0
            for c in batch:
                if c.short_hash not in all_commits:
                    all_commits[c.short_hash] = c
                    new_count += 1
                    if is_merge:
                        merge_hashes.add(c.short_hash)
            dup_count = len(batch) - new_count
            if debug:
                label = "merges" if is_merge else "no-merges"
                print(f"    [{author}] {label}: {new_count} nuevos ({dup_count} duplicados)")

    non_merges = [c for c in all_commits.values() if c.short_hash not in merge_hashes]
    merges = [c for c in all_commits.values() if c.short_hash in merge_hashes]

    result = non_merges + (merges if not exclude_merges else [])
    return result, len(merge_hashes), merge_hashes


def extract_stats(repo_root: Path, authors: list[str], start_date: str, end_date: str) -> tuple[int, int]:
    """Return (added_lines, deleted_lines) for the given repo and date range.

    Sums stats across all author patterns."""
    added = deleted = 0
    for author in authors:
        cmd = [
            "git", "log", "-m",
            f"--author={author}",
            f"--since={start_date}",
            f"--until={end_date}T23:59:59",
            "--shortstat",
            "--format=",
        ]

        result = subprocess.run(
            cmd, cwd=str(repo_root), capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            continue

        for line in result.stdout.strip().splitlines():
            # Each non-empty line: "X files changed, Y insertions(+), Z deletions(-)"
            for part in line.split(","):
                part = part.strip()
                m_add = re.search(r"(\d+) insertion", part)
                m_del = re.search(r"(\d+) deletion", part)
                if m_add:
                    added += int(m_add.group(1))
                if m_del:
                    deleted += int(m_del.group(1))
    return added, deleted
