"""Generación del informe Markdown."""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from string import Template

from gitrack.models import RepoResult

_DEFAULT_TEMPLATE_PATH = Path(__file__).parent / "report_template.md"
_REPO_BLOCK_START = "<!-- #repo_block -->"
_REPO_BLOCK_END = "<!-- #/repo_block -->"


def _load_templates() -> tuple[Template, str]:
    """Load the bundled template file and extract the repo block section.

    The repo block sits inline as a visual guide for where rendered blocks go.
    Returns (report_template_with_placeholder, repo_block_template_string).
    The marked section is replaced with $repositories_commit_analysis."""
    raw = _DEFAULT_TEMPLATE_PATH.read_text(encoding="utf-8")

    start_idx = raw.index(_REPO_BLOCK_START)
    end_idx = raw.index(_REPO_BLOCK_END) + len(_REPO_BLOCK_END)
    repo_block = raw[start_idx + len(_REPO_BLOCK_START):end_idx - len(_REPO_BLOCK_END)].strip()

    # Replace the entire marked section with the placeholder variable.
    report_body = (
        raw[:start_idx].rstrip() + "\n$repositories_commit_analysis" + raw[end_idx:]
    )

    return Template(report_body), repo_block


_GITRACK_HASH_PREFIX = "<!-- gitrack-hash: "
_GITRACK_HASH_SUFFIX = ' -->\n'


def _content_hash(text: str) -> str:
    """Return a short SHA-256 hex digest of *text*."""
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def read_existing_hash(path: Path) -> str | None:
    """Read the embedded gitrack hash from an existing file, or None."""
    # splitlines() strips \n, so match against ' -->' (without newline)
    _SUFFIX_MATCH = " -->"
    try:
        for line in reversed(path.read_text(encoding="utf-8").splitlines()):
            stripped = line.strip()
            if stripped.startswith(_GITRACK_HASH_PREFIX) and stripped.endswith(
                _SUFFIX_MATCH
            ):
                return stripped[len(_GITRACK_HASH_PREFIX):-len(_SUFFIX_MATCH)]
    except (FileNotFoundError, OSError):
        pass
    return None


def write_report(path: Path, content_body: str, new_hash: str) -> bool:
    """Write the report file with embedded hash.

    Returns True if the file was written, False if skipped (content unchanged)."""
    existing_hash = read_existing_hash(path)

    if existing_hash == new_hash:
        print(f"\nContenido sin cambios (hash {new_hash}). Saltando escritura del MD.")
        return False

    full_content = (
        content_body + "\n"
        + _GITRACK_HASH_PREFIX + new_hash + _GITRACK_HASH_SUFFIX
    )
    path.write_text(full_content, encoding="utf-8")
    return True


def _build_commit_rows(repo: RepoResult, mark_merges: bool) -> str:
    """Build the Markdown commit rows for a single repository."""
    lines: list[str] = []
    for c in repo.commits:
        is_merge = c.short_hash in repo.merge_hashes
        if mark_merges or not is_merge:
            prefix = " (Merge)" if is_merge else ""
            lines.append(f"| `{c.short_hash}`{prefix} | {c.date} | {c.message} |")
    return "\n".join(lines)


def _build_repo_block(repo: RepoResult, mark_merges: bool, repo_template: str) -> str:
    """Build the Markdown block for a single repository using *repo_template*."""
    tpl = Template(repo_template)
    commit_rows = _build_commit_rows(repo, mark_merges)
    return tpl.substitute(
        repository_name=repo.name,
        repository_commits_count=repo.total,
        repository_lines_added=repo.added,
        repository_lines_deleted=repo.deleted,
        repository_merge_commits_count=repo.merges,
        repository_commit_rows=commit_rows,
    )


def generate_report_md(
    results: list[RepoResult],
    author: str,
    start_date: str,
    end_date: str,
    root_dir: str,
    mark_merges: bool = False,
) -> tuple[str, str]:
    """Build the report content in Markdown format using a template.

    Returns (content_without_hash, hash_value).
    The hash is computed over *content_without_hash* so it stays stable.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S %z")

    repositories_count = len(results)
    commits_count = sum(r.total for r in results)
    merge_commits_count = sum(r.merges for r in results)
    total_lines_added = sum(r.added for r in results)
    total_lines_deleted = sum(r.deleted for r in results)

    tpl, repo_block_template = _load_templates()

    # Build per-repository blocks (sorted alphabetically)
    repo_blocks: list[str] = []
    for repo in sorted(results, key=lambda r: r.name):
        repo_blocks.append(_build_repo_block(repo, mark_merges, repo_block_template))

    repositories_commit_analysis = "\n\n".join(repo_blocks)

    # Render template
    content = tpl.substitute(
        report_title="Informe de Actividad Git — Período Laboral",
        authors_displayed=author,
        analysis_date_range=f"{start_date} → {end_date}",
        report_generated_at=now,
        repositories_count=repositories_count,
        commits_count=commits_count,
        merge_commits_count=merge_commits_count,
        total_lines_added=total_lines_added,
        total_lines_deleted=total_lines_deleted,
        repositories_commit_analysis=repositories_commit_analysis,
    )

    return content, _content_hash(content)
