"""Tests para report.py — bug de conteo con --no-merges.

Cuando exclude_merges=True, extract_commits() devuelve solo commits no-merge
en la lista, pero SÍ reporta merge_count y merge_hashes. El reporte debe usar
repo.total directamente (que ya excluye merges) en lugar de restar repo.merges
otra vez.

Bug reproducido: header muestra conteo erróneo (incluso negativo) porque
non_merges = repo.total - repo.merges double-resta los merges.
"""

import unittest
from io import StringIO
import sys

from gitrack.models import Commit, RepoResult


class TestReportNoMerges(unittest.TestCase):
    """Verify header count matches table rows when --no-merges is used."""

    def _capture_warnings(self, func, *args, **kwargs):
        """Run *func* and capture any [WARN] lines printed to stdout."""
        old = sys.stdout
        sys.stdout = buf = StringIO()
        try:
            func(*args, **kwargs)
        finally:
            sys.stdout = old
        return buf.getvalue()

    # ------------------------------------------------------------------ helpers

    def _make_repo_with_excluded_merges(self):
        """Build a RepoResult that simulates --no-merges output.

        The commits list contains ONLY non-merge commits (5), but merge_count=2
        and merge_hashes has 2 entries — exactly what extract_commits() returns
        when exclude_merges=True."""
        return RepoResult(
            name="test-repo",
            commits=[
                Commit("abc1234", "2025-06-01", "feat: add login"),
                Commit("def5678", "2025-06-02", "fix: typo in README"),
                Commit("ghi9012", "2025-06-03", "chore: update deps"),
                Commit("jkl3456", "2025-06-04", "feat: add logout"),
                Commit("mno7890", "2025-06-05", "fix: null pointer"),
            ],
            added=100,
            deleted=50,
            merges=2,                          # merge commits found but excluded from list
            merge_hashes={"mergeA", "mergeB"},  # none of these appear in commits list
        )

    def _make_repo_all_merges_excluded(self):
        """Repo where ALL commits are merges — header should show 0."""
        return RepoResult(
            name="all-merges-repo",
            commits=[],                         # all were merges, excluded from list
            added=0,
            deleted=0,
            merges=2,
            merge_hashes={"m1", "m2"},
        )

    def _make_repo_with_merges_included(self):
        """Build a RepoResult when --no-merges is NOT used (mark_merges=True).

        The commits list contains BOTH non-merge AND merge commits."""
        return RepoResult(
            name="with-merges-repo",
            commits=[
                Commit("abc1234", "2025-06-01", "feat: add login"),
                Commit("def5678", "2025-06-02", "fix: typo in README"),
                Commit("mergeA",  "2025-06-03", "Merge branch 'feature'"),
                Commit("ghi9012", "2025-06-04", "chore: update deps"),
                Commit("mergeB",  "2025-06-05", "Merge pull request #42"),
            ],
            added=100,
            deleted=50,
            merges=2,
            merge_hashes={"mergeA", "mergeB"},
        )

    # ------------------------------------------------------------------ tests

    def test_header_matches_table_when_no_merges(self):
        """Header commit count must equal table row count with --no-merges."""
        from gitrack.report import generate_report_md

        repo = self._make_repo_with_excluded_merges()
        warnings = self._capture_warnings(
            generate_report_md, [repo], "test@user.com", "2025-01-01", "2025-12-31", "/tmp"
        )

        self.assertNotIn("[WARN]", warnings,
                         f"Unexpected warning (header/table mismatch): {warnings.strip()}")

    def test_header_is_not_negative_when_no_merges(self):
        """Header must never show a negative commit count.

        Reproduces the exact case from terraform-modules:
          total=2, merges=15 → header showed -13 commits (BUG)"""
        from gitrack.report import generate_report_md

        repo = RepoResult(
            name="terraform-modules",
            commits=[
                Commit("h1", "2025-06-01", "feat: module"),
                Commit("h2", "2025-06-02", "fix: typo"),
            ],
            added=30, deleted=10,
            merges=15,
            merge_hashes=set(f"m{i}" for i in range(15)),
        )

        content, _ = generate_report_md([repo], "test@user.com", "2025-01-01",
                                         "2025-12-31", "/tmp")

        # Header line should NOT contain a negative number before "commits"
        for line in content.splitlines():
            if "`terraform-modules`" in line and "commits" in line:
                self.assertNotIn("-13 commits", line,
                                 f"Header shows negative commit count: {line}")
                self.assertIn("2 commits", line,
                              f"Header should show 2 (non-merge) commits: {line}")
                break

    def test_header_zero_when_all_commits_are_merges(self):
        """When all commits are merges and excluded, header shows 0."""
        from gitrack.report import generate_report_md

        repo = self._make_repo_all_merges_excluded()
        content, _ = generate_report_md([repo], "test@user.com", "2025-01-01",
                                         "2025-12-31", "/tmp")

        for line in content.splitlines():
            if "`all-merges-repo`" in line and "commits" in line:
                self.assertIn("0 commits", line,
                              f"Header should show 0 commits: {line}")
                break

    def test_table_rows_equal_header_when_no_merges(self):
        """Count table rows and verify they match the header count."""
        from gitrack.report import generate_report_md

        repo = self._make_repo_with_excluded_merges()
        content, _ = generate_report_md([repo], "test@user.com", "2025-01-01",
                                         "2025-12-31", "/tmp")

        lines = content.splitlines()
        # Find the header line for test-repo
        header_count = None
        table_row_count = 0
        in_table = False
        for line in lines:
            if "`test-repo`" in line and "commits" in line:
                # Extract number before "commits"
                parts = line.split("— ")[1]
                header_count = int(parts.split()[0])
            elif "|------|-------|---------|" in line:
                in_table = True
            elif in_table:
                if line.startswith("|"):
                    table_row_count += 1
                else:
                    break

        self.assertEqual(header_count, table_row_count,
                         f"Header ({header_count}) != table rows ({table_row_count})")

    def test_no_warnings_for_excluded_merges(self):
        """No [WARN] lines should be printed when --no-merges excludes merges."""
        from gitrack.report import generate_report_md

        repos = [
            self._make_repo_with_excluded_merges(),
            self._make_repo_all_merges_excluded(),
            RepoResult(
                name="zero-merges",
                commits=[Commit("h1", "2025-06-01", "init")],
                added=10, deleted=0, merges=0, merge_hashes=set(),
            ),
        ]

        warnings = self._capture_warnings(
            generate_report_md, repos, "test@user.com", "2025-01-01", "2025-12-31", "/tmp"
        )

        self.assertNotIn("[WARN]", warnings,
                         f"Unexpected warnings: {warnings.strip()}")

    # ------------------------------------------------------------------ mark_merges mode (no double-subtract)

    def test_mark_merges_header_shows_total(self):
        """With mark_merges=True, header should show total commits including merges."""
        from gitrack.report import generate_report_md

        repo = self._make_repo_with_merges_included()
        content, _ = generate_report_md([repo], "test@user.com", "2025-01-01",
                                         "2025-12-31", "/tmp", mark_merges=True)

        for line in content.splitlines():
            if "`with-merges-repo`" in line and "commits" in line:
                self.assertIn("5 commits", line,
                              f"Header should show total (5) commits: {line}")
                break

    def test_mark_merges_table_excludes_merge_rows(self):
        """With mark_merges=True, table includes ALL rows (merges marked)."""
        from gitrack.report import generate_report_md

        repo = self._make_repo_with_merges_included()
        content, _ = generate_report_md([repo], "test@user.com", "2025-01-01",
                                         "2025-12-31", "/tmp", mark_merges=True)

        lines = content.splitlines()
        table_row_count = 0
        in_table = False
        for line in lines:
            if "|------|-------|---------|" in line:
                in_table = True
            elif in_table:
                if line.startswith("|"):
                    table_row_count += 1
                else:
                    break

        self.assertEqual(table_row_count, 5,
                         f"Expected 5 rows (3 non-merge + 2 merge), got {table_row_count}")


if __name__ == "__main__":
    unittest.main()
