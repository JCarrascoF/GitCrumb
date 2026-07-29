from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Commit:
    """Represents a commit extracted from git log."""
    short_hash: str
    date: str       # YYYY-MM-DD
    message: str


@dataclass
class RepoResult:
    """Result of analyzing a repository."""
    name: str      # relative path to ROOT_DIR
    commits: list[Commit] = field(default_factory=list)
    added: int = 0
    deleted: int = 0
    merges: int = 0
    merge_hashes: set[str] = field(default_factory=set)

    @property
    def total(self) -> int:
        return len(self.commits)
