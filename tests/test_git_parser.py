"""Tests para git_parser.py — parseo de git log y estadísticas."""

import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from gitrack.models import Commit
from gitrack.git_parser import _parse_log, extract_commits, extract_stats


class TestParseLog(unittest.TestCase):
    def test_parses_valid_lines(self):
        output = "a1b2c3d|2025-03-15|Fix login timeout\ne4f5a6b|2025-03-16|Add validation"
        commits = _parse_log(output)
        self.assertEqual(len(commits), 2)
        self.assertEqual(commits[0].short_hash, "a1b2c3d")
        self.assertEqual(commits[0].date, "2025-03-15")
        self.assertEqual(commits[0].message, "Fix login timeout")
        self.assertEqual(commits[1].short_hash, "e4f5a6b")

    def test_empty_output(self):
        self.assertEqual(_parse_log(""), [])
        self.assertEqual(_parse_log("\n"), [])

    def test_malformed_lines_skipped(self):
        output = "good|2025-01-01|Message\nbad_line_no_pipes\nalso-bad"
        commits = _parse_log(output)
        self.assertEqual(len(commits), 1)
        self.assertEqual(commits[0].short_hash, "good")

    def test_message_with_pipes(self):
        output = "abc|2025-06-01|Merge branch 'feat|x'"
        commits = _parse_log(output)
        self.assertEqual(len(commits), 1)
        self.assertEqual(commits[0].message, "Merge branch 'feat|x'")


class TestExtractCommits(unittest.TestCase):

    @patch("gitrack.git_parser._git_log")
    def test_deduplication_by_hash(self, mock_git_log):
        """Commits con el mismo hash no se duplican."""
        shared = Commit("dup1", "2025-03-01", "Shared commit")
        unique_a = Commit("a1", "2025-03-02", "Author A only")
        mock_git_log.side_effect = [
            [shared, unique_a],   # author 1, --no-merges
            [],                    # author 1, --merges
            [shared],              # author 2, --no-merges (duplicate)
            [],                    # author 2, --merges
        ]

        commits, merge_count, merge_hashes = extract_commits(
            Path("/tmp/repo"), ["author_a", "author_b"],
            "2025-01-01", "2025-12-31",
        )
        self.assertEqual(len(commits), 2)
        hashes = {c.short_hash for c in commits}
        self.assertIn("dup1", hashes)
        self.assertIn("a1", hashes)

    @patch("gitrack.git_parser._git_log")
    def test_merge_detection(self, mock_git_log):
        """Los merges se detectan y cuentan correctamente."""
        regular = Commit("r1", "2025-03-01", "Regular commit")
        merge_c = Commit("m1", "2025-03-02", "Merge branch 'dev'")
        mock_git_log.side_effect = [
            [regular],             # author, --no-merges
            [merge_c],             # author, --merges
        ]

        commits, merge_count, merge_hashes = extract_commits(
            Path("/tmp/repo"), ["author"], "2025-01-01", "2025-12-31",
        )
        self.assertEqual(len(commits), 2)
        self.assertEqual(merge_count, 1)
        self.assertIn("m1", merge_hashes)

    @patch("gitrack.git_parser._git_log")
    def test_exclude_merges(self, mock_git_log):
        """Cuando exclude_merges=True, los merges no aparecen en el resultado."""
        regular = Commit("r1", "2025-03-01", "Regular commit")
        merge_c = Commit("m1", "2025-03-02", "Merge branch 'dev'")
        mock_git_log.side_effect = [
            [regular],             # --no-merges
            [merge_c],             # --merges
        ]

        commits, merge_count, _ = extract_commits(
            Path("/tmp/repo"), ["author"], "2025-01-01", "2025-12-31",
            exclude_merges=True,
        )
        self.assertEqual(len(commits), 1)
        self.assertEqual(commits[0].short_hash, "r1")
        # merge_count sigue reflejando merges encontrados
        self.assertEqual(merge_count, 1)

    @patch("gitrack.git_parser._git_log")
    def test_no_commits(self, mock_git_log):
        mock_git_log.return_value = []
        commits, mc, mh = extract_commits(
            Path("/tmp/repo"), ["nobody"], "2025-01-01", "2025-12-31",
        )
        self.assertEqual(commits, [])
        self.assertEqual(mc, 0)
        self.assertEqual(mh, set())


class TestExtractStats(unittest.TestCase):

    @patch("gitrack.git_parser.subprocess.run")
    def test_parses_insertions_and_deletions(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "3 files changed, 150 insertions(+), 42 deletions(-)\n"
            "1 file changed, 10 insertions(+)"
        )
        mock_run.return_value = mock_result

        added, deleted = extract_stats(
            Path("/tmp/repo"), ["author"], "2025-01-01", "2025-12-31",
        )
        self.assertEqual(added, 160)
        self.assertEqual(deleted, 42)

    @patch("gitrack.git_parser.subprocess.run")
    def test_zero_stats(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        added, deleted = extract_stats(
            Path("/tmp/repo"), ["author"], "2025-01-01", "2025-12-31",
        )
        self.assertEqual(added, 0)
        self.assertEqual(deleted, 0)

    @patch("gitrack.git_parser.subprocess.run")
    def test_git_error_returns_zero(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        added, deleted = extract_stats(
            Path("/tmp/repo"), ["author"], "2025-01-01", "2025-12-31",
        )
        self.assertEqual(added, 0)
        self.assertEqual(deleted, 0)

    @patch("gitrack.git_parser.subprocess.run")
    def test_multiple_authors_summed(self, mock_run):
        """Stats de múltiples autores se suman."""
        results = [
            MagicMock(returncode=0, stdout="1 file changed, 50 insertions(+), 10 deletions(-)"),
            MagicMock(returncode=0, stdout="2 files changed, 30 insertions(+), 5 deletions(-)"),
        ]
        mock_run.side_effect = results

        added, deleted = extract_stats(
            Path("/tmp/repo"), ["author_a", "author_b"],
            "2025-01-01", "2025-12-31",
        )
        self.assertEqual(added, 80)
        self.assertEqual(deleted, 15)


if __name__ == "__main__":
    unittest.main()
