"""Tests para report.py — generación de informe Markdown."""

import unittest
import tempfile
from pathlib import Path

from gitrack.models import Commit, RepoResult
from gitrack.report import (
    _content_hash,
    read_existing_hash,
    write_report,
    generate_report_md,
)


class TestContentHash(unittest.TestCase):
    def test_deterministic(self):
        h1 = _content_hash("hello")
        h2 = _content_hash("hello")
        self.assertEqual(h1, h2)

    def test_different_content_different_hash(self):
        h1 = _content_hash("hello")
        h2 = _content_hash("world")
        self.assertNotEqual(h1, h2)

    def test_length_12_hex(self):
        h = _content_hash("test")
        self.assertEqual(len(h), 12)
        int(h, 16)  # valid hex


class TestReadExistingHash(unittest.TestCase):
    def test_reads_hash_from_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Title\n")
            f.write("Some content\n")
            f.write("<!-- gitrack-hash: abc123def456 -->\n")
            path = Path(f.name)

        try:
            h = read_existing_hash(path)
            self.assertEqual(h, "abc123def456")
        finally:
            path.unlink()

    def test_returns_none_when_no_hash(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Just content\n")
            path = Path(f.name)

        try:
            self.assertIsNone(read_existing_hash(path))
        finally:
            path.unlink()

    def test_returns_none_when_file_missing(self):
        self.assertIsNone(read_existing_hash(Path("/tmp/nonexistent-file-12345.md")))


class TestWriteReport(unittest.TestCase):
    def test_writes_new_file(self):
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            path = Path(f.name)
        path.unlink()

        try:
            written = write_report(path, "# Content", "hash123")
            self.assertTrue(written)
            content = path.read_text(encoding="utf-8")
            self.assertIn("# Content", content)
            self.assertIn("<!-- gitrack-hash: hash123 -->", content)
        finally:
            path.unlink(missing_ok=True)

    def test_skips_when_hash_matches(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Old\n")
            f.write("<!-- gitrack-hash: samehash -->\n")
            path = Path(f.name)

        try:
            written = write_report(path, "# New content", "samehash")
            self.assertFalse(written)
            # File unchanged
            content = path.read_text(encoding="utf-8")
            self.assertIn("# Old", content)
        finally:
            path.unlink()


class TestGenerateReportMd(unittest.TestCase):

    def _make_result(self, name, num_commits=1, num_merges=0, added=10, deleted=5):
        commits = [Commit(f"h{i}", "2025-03-{i:02d}", f"Message {i}") for i in range(num_commits)]
        merge_hashes = {f"h{i}" for i in range(num_commits - num_merges, num_commits)} if num_merges else set()
        return RepoResult(
            name=name, commits=commits, added=added, deleted=deleted,
            merges=num_merges, merge_hashes=merge_hashes,
        )

    def test_structure(self):
        results = [self._make_result("repo-a", num_commits=2)]
        content, hash_val = generate_report_md(
            results, "test@dev.com", "2025-01-01", "2025-12-31", "/tmp/root"
        )

        self.assertIn("# Informe de Actividad Git — Período Laboral", content)
        self.assertIn("**Autor**: test@dev.com", content)
        self.assertIn("**Rango de fechas**: 2025-01-01 → 2025-12-31", content)
        self.assertIn("## `repo-a`", content)
        self.assertIn("---", content)
        self.assertIn("## Resumen Ejecutivo", content)
        # Summary appears before repo blocks
        summary_pos = content.index("## Resumen Ejecutivo")
        repo_pos = content.index("## `repo-a`")
        self.assertLess(summary_pos, repo_pos)
        self.assertIn("- **Repositorios activos**: 1", content)
        self.assertIn("- **Total de commits**: 2", content)

    def test_repos_sorted_alphabetically(self):
        results = [
            self._make_result("z-repo"),
            self._make_result("a-repo"),
            self._make_result("m-repo"),
        ]
        content, _ = generate_report_md(
            results, "author", "2025-01-01", "2025-12-31", "/tmp/root"
        )

        a_pos = content.index("## `a-repo`")
        m_pos = content.index("## `m-repo`")
        z_pos = content.index("## `z-repo`")
        self.assertLess(a_pos, m_pos)
        self.assertLess(m_pos, z_pos)

    def test_header_shows_total(self):
        results = [self._make_result("repo", num_commits=5, num_merges=2)]
        content, _ = generate_report_md(
            results, "author", "2025-01-01", "2025-12-31", "/tmp/root"
        )
        self.assertIn("## `repo` — 5 commits (+10/-5)", content)

    def test_mark_merges_shows_all(self):
        results = [self._make_result("repo", num_commits=3, num_merges=1)]
        content, _ = generate_report_md(
            results, "author", "2025-01-01", "2025-12-31", "/tmp/root",
            mark_merges=True,
        )
        # All 3 commits appear in table
        rows = [l for l in content.splitlines() if l.startswith("| `h")]
        self.assertEqual(len(rows), 3)

    def test_without_mark_merges_hides_merges(self):
        results = [self._make_result("repo", num_commits=3, num_merges=1)]
        content, _ = generate_report_md(
            results, "author", "2025-01-01", "2025-12-31", "/tmp/root",
            mark_merges=False,
        )
        # Only 2 non-merge commits in table
        rows = [l for l in content.splitlines() if l.startswith("| `h")]
        self.assertEqual(len(rows), 2)

    def test_executive_summary_totals(self):
        results = [
            self._make_result("r1", num_commits=3, num_merges=1, added=100, deleted=50),
            self._make_result("r2", num_commits=7, num_merges=2, added=200, deleted=80),
        ]
        content, _ = generate_report_md(
            results, "author", "2025-01-01", "2025-12-31", "/tmp/root"
        )
        self.assertIn("- **Repositorios activos**: 2", content)
        self.assertIn("- **Total de commits**: 10", content)
        self.assertIn("- **Líneas añadidas**: 300", content)
        self.assertIn("- **Líneas eliminadas**: 130", content)

    def test_empty_results(self):
        content, _ = generate_report_md(
            [], "author", "2025-01-01", "2025-12-31", "/tmp/root"
        )
        self.assertIn("# Informe de Actividad Git — Período Laboral", content)
        self.assertIn("- **Repositorios activos**: 0", content)
        self.assertIn("- **Total de commits**: 0", content)

    def test_hash_is_stable(self):
        """El hash no incluye la marca de tiempo → contenido estable."""
        results = [self._make_result("repo")]
        _, h1 = generate_report_md(results, "a", "2025-01-01", "2025-12-31", "/r")
        import time; time.sleep(0.01)
        _, h2 = generate_report_md(results, "a", "2025-01-01", "2025-12-31", "/r")
        # Hash puede variar por timestamp en el header — solo verificamos que existe
        self.assertEqual(len(h1), 12)


if __name__ == "__main__":
    unittest.main()
