"""Tests para repo_analyzer.py — búsqueda de repos y análisis."""

import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

from gitrack.models import Commit, RepoResult


class TestFindGitRoot(unittest.TestCase):

    @patch("gitrack.repo_analyzer.subprocess.run")
    def test_returns_root_when_git_found(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "/home/user/project\n"
        mock_run.return_value = mock_result

        from gitrack.repo_analyzer import _find_git_root
        root = _find_git_root(Path("/home/user/project/src"))
        self.assertEqual(root, Path("/home/user/project"))

    @patch("gitrack.repo_analyzer.subprocess.run")
    def test_returns_none_when_not_git(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        from gitrack.repo_analyzer import _find_git_root
        root = _find_git_root(Path("/tmp/not-a-repo"))
        self.assertIsNone(root)

    @patch("gitrack.repo_analyzer.subprocess.run")
    def test_returns_none_on_exception(self, mock_run):
        mock_run.side_effect = FileNotFoundError()

        from gitrack.repo_analyzer import _find_git_root
        root = _find_git_root(Path("/tmp/missing"))
        self.assertIsNone(root)


class TestIsIgnoredByParent(unittest.TestCase):

    @patch("gitrack.repo_analyzer._find_git_root")
    def test_ignored_path(self, mock_find_root):
        mock_find_root.return_value = Path("/home/user/project")

        with patch("gitrack.repo_analyzer.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)  # ignored
            from gitrack.repo_analyzer import _is_ignored_by_parent
            result = _is_ignored_by_parent(Path("/home/user/project/.terraform"))
            self.assertTrue(result)

    @patch("gitrack.repo_analyzer._find_git_root")
    def test_not_ignored_path(self, mock_find_root):
        mock_find_root.return_value = Path("/home/user/project")

        with patch("gitrack.repo_analyzer.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)  # not ignored
            from gitrack.repo_analyzer import _is_ignored_by_parent
            result = _is_ignored_by_parent(Path("/home/user/project/src"))
            self.assertFalse(result)

    @patch("gitrack.repo_analyzer._find_git_root")
    def test_no_parent_repo(self, mock_find_root):
        mock_find_root.return_value = None
        from gitrack.repo_analyzer import _is_ignored_by_parent
        result = _is_ignored_by_parent(Path("/tmp/orphan"))
        self.assertFalse(result)

    @patch("gitrack.repo_analyzer._find_git_root")
    def test_candidate_is_repo_root(self, mock_find_root):
        """Si el candidato ES la raíz del repo ancestro, no se filtra."""
        # _is_ignored_by_parent calls _find_git_root on the parent directory
        mock_find_root.return_value = Path("/home/user/project/.terraform")

        with patch("gitrack.repo_analyzer.subprocess.run") as mock_run:
            from gitrack.repo_analyzer import _is_ignored_by_parent
            result = _is_ignored_by_parent(Path("/home/user/project/.terraform"))
            # candidate == git_root → False (no subprocess call needed)
            self.assertFalse(result)


class TestFindRepos(unittest.TestCase):

    @patch("gitrack.repo_analyzer._is_ignored_by_parent")
    def test_finds_repos(self, mock_ignored):
        mock_ignored.return_value = False

        # Create fake .git dirs
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "repo-a" / ".git").mkdir(parents=True)
            (Path(tmpdir) / "repo-b" / ".git").mkdir(parents=True)
            # Non-dir .git should be skipped
            not_repo_dir = Path(tmpdir) / "not-repo"
            not_repo_dir.mkdir(parents=True)
            (not_repo_dir / ".git").touch()

            from gitrack.repo_analyzer import find_repos
            repos = find_repos(tmpdir)
            self.assertEqual(len(repos), 2)
            names = {r.name for r in repos}
            self.assertIn("repo-a", names)
            self.assertIn("repo-b", names)

    @patch("gitrack.repo_analyzer._is_ignored_by_parent")
    def test_filters_ignored(self, mock_ignored):
        """Los repos ignorados por .gitignore se excluyen."""
        # Return True for the second repo
        call_count = {"n": 0}

        def side_effect(path):
            call_count["n"] += 1
            return path.name == "ignored-repo"

        mock_ignored.side_effect = side_effect

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "good-repo" / ".git").mkdir(parents=True)
            (Path(tmpdir) / "ignored-repo" / ".git").mkdir(parents=True)

            from gitrack.repo_analyzer import find_repos
            repos = find_repos(tmpdir)
            self.assertEqual(len(repos), 1)
            self.assertEqual(repos[0].name, "good-repo")


class TestAnalyzeRepositories(unittest.TestCase):

    @patch("gitrack.repo_analyzer.find_repos")
    @patch("gitrack.repo_analyzer.extract_commits")
    @patch("gitrack.repo_analyzer.extract_stats")
    def test_returns_results_with_commits(self, mock_stats, mock_commits, mock_find):
        mock_find.return_value = [Path("/tmp/root/repo-a")]
        commits = [Commit("h1", "2025-03-01", "Msg")]
        mock_commits.return_value = (commits, 0, set())
        mock_stats.return_value = (100, 50)

        from gitrack.repo_analyzer import analyze_repositories
        results = analyze_repositories("/tmp/root", ["author"], "2025-01-01", "2025-12-31")

        self.assertEqual(len(results), 1)
        r = results[0]
        self.assertEqual(r.name, "repo-a")
        self.assertEqual(r.total, 1)
        self.assertEqual(r.added, 100)
        self.assertEqual(r.deleted, 50)

    @patch("gitrack.repo_analyzer.find_repos")
    @patch("gitrack.repo_analyzer.extract_commits")
    def test_skips_repos_without_commits(self, mock_commits, mock_find):
        mock_find.return_value = [Path("/tmp/root/empty-repo")]
        mock_commits.return_value = ([], 0, set())

        from gitrack.repo_analyzer import analyze_repositories
        results = analyze_repositories("/tmp/root", ["author"], "2025-01-01", "2025-12-31")
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
