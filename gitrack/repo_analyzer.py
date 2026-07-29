"""Lógica de análisis de historial — encontrar repos, extraer commits, estadísticas."""

from __future__ import annotations

import subprocess
from pathlib import Path

from gitrack.git_parser import extract_commits, extract_stats
from gitrack.models import RepoResult


def _find_git_root(repo: Path) -> Path | None:
    """Return the root of the git repository containing *repo*.

    Walks upward until a .git directory is found. Returns None if not found."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return None


def _is_ignored_by_parent(candidate: Path) -> bool:
    """Check whether *candidate* is inside a path ignored by the nearest
    ancestor git repository (not candidate itself).

    Runs `git check-ignore` from the immediate parent's git root to respect
    .gitignore / exclude patterns of the containing repo (e.g. a Terraform
    module whose .gitignore excludes .terraform/)."""
    parent = candidate.parent
    git_root = _find_git_root(parent)
    if git_root is None:
        return False
    # Don't filter if candidate IS the ancestor repo root itself
    if candidate == git_root:
        return False
    try:
        result = subprocess.run(
            ["git", "check-ignore", "--quiet", "--", str(candidate)],
            cwd=str(git_root),
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def find_repos(root_dir: str) -> list[Path]:
    """Recursively search for .git directories and return each repo root.

    Filters out candidates falling inside paths ignored by .gitignore or
    .git/info/exclude of the nearest ancestor repository.
    """
    root_path = Path(root_dir).expanduser()
    repos: list[Path] = []
    for git_dir in root_path.rglob(".git"):
        if not git_dir.is_dir():
            continue
        candidate = git_dir.parent
        # Skip if an ancestor repo ignores this path (e.g. .terraform/)
        if _is_ignored_by_parent(candidate):
            continue
        repos.append(candidate)
    return sorted(repos)


def analyze_repositories(root_dir: str, authors: list[str], start_date: str, end_date: str,
                         exclude_merges: bool = False, debug: bool = False) -> list[RepoResult]:
    """Walk all repos and return only those with commits in the date range."""
    repos = find_repos(root_dir)
    results: list[RepoResult] = []

    for repo in repos:
        rel_name = str(repo.relative_to(Path(root_dir).expanduser()))
        print(f"  Procesando: {rel_name} ...")

        commits, merge_count, merge_hashes = extract_commits(
            repo, authors, start_date, end_date, exclude_merges, debug=debug,
        )
        if commits:
            added, deleted = extract_stats(repo, authors, start_date, end_date)
            results.append(RepoResult(
                name=rel_name,
                commits=commits,
                added=added,
                deleted=deleted,
                merges=merge_count,
                merge_hashes=merge_hashes,
            ))

    return results
