"""Tests para docker_export.py — exportación PDF vía Docker."""

import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestCheckDocker(unittest.TestCase):

    @patch("gitcrumb.docker_export.subprocess.run")
    def test_docker_available(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        from gitcrumb.docker_export import check_docker
        self.assertTrue(check_docker())

    @patch("gitcrumb.docker_export.subprocess.run")
    def test_docker_not_available(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        from gitcrumb.docker_export import check_docker
        self.assertFalse(check_docker())

    @patch("gitcrumb.docker_export.subprocess.run")
    def test_docker_not_installed(self, mock_run):
        mock_run.side_effect = FileNotFoundError()
        from gitcrumb.docker_export import check_docker
        self.assertFalse(check_docker())


class TestEnsureImage(unittest.TestCase):

    @patch("gitcrumb.docker_export.subprocess.run")
    def test_image_already_present(self, mock_run):
        """Si inspect devuelve 0, no se hace pull."""
        mock_run.return_value = MagicMock(returncode=0)
        from gitcrumb.docker_export import ensure_image
        result = ensure_image("marpteam/marp-cli")
        self.assertTrue(result)
        # Solo una llamada (inspect), no pull
        calls = [c for c in mock_run.call_args_list]
        self.assertEqual(len(calls), 1)

    @patch("gitcrumb.docker_export.subprocess.run")
    def test_pulls_when_missing(self, mock_run):
        """Si inspect falla, se hace pull."""
        mock_run.side_effect = [
            MagicMock(returncode=1),   # inspect fails
            MagicMock(returncode=0),   # pull succeeds
        ]
        from gitcrumb.docker_export import ensure_image
        result = ensure_image("marpteam/marp-cli")
        self.assertTrue(result)
        self.assertEqual(len(mock_run.call_args_list), 2)

    @patch("gitcrumb.docker_export.subprocess.run")
    def test_pull_fails(self, mock_run):
        mock_run.side_effect = [
            MagicMock(returncode=1),   # inspect fails
            MagicMock(returncode=1, stderr="timeout"),  # pull fails
        ]
        from gitcrumb.docker_export import ensure_image
        result = ensure_image("marpteam/marp-cli")
        self.assertFalse(result)


class TestExportPdf(unittest.TestCase):

    @patch("gitcrumb.docker_export.subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)

        with patch.object(Path, "exists", return_value=True):
            import tempfile
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
                f.write("# Test Report\n")
                md_path = Path(f.name)

            try:
                from gitcrumb.docker_export import export_pdf
                pdf_path = export_pdf(str(md_path))
                self.assertIsNotNone(pdf_path)
                self.assertTrue(pdf_path.endswith(".pdf"))
            finally:
                md_path.unlink()
                md_path.with_suffix(".pdf").unlink(missing_ok=True)

    @patch("gitcrumb.docker_export.subprocess.run")
    def test_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr=b"error")

        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test Report\n")
            md_path = Path(f.name)

        try:
            from gitcrumb.docker_export import export_pdf
            result = export_pdf(str(md_path))
            self.assertIsNone(result)
        finally:
            md_path.unlink()

    @patch("gitcrumb.docker_export.subprocess.run")
    def test_cleans_up_marp_file(self, mock_run):
        """El archivo .marp.md intermedio se elimina incluso en error."""
        mock_run.return_value = MagicMock(returncode=1)

        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test\n")
            md_path = Path(f.name)

        try:
            from gitcrumb.docker_export import export_pdf
            export_pdf(str(md_path))
            # .marp.md should be cleaned up
            marp_name = str(md_path.name).replace(".md", ".marp.md")
            self.assertFalse((md_path.parent / marp_name).exists())
        finally:
            md_path.unlink()

    @patch("gitcrumb.docker_export.subprocess.run")
    def test_prepends_frontmatter(self, mock_run):
        """El contenido del archivo .marp.md incluye el frontmatter."""
        mock_run.return_value = MagicMock(returncode=0)

        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Original\n")
            md_path = Path(f.name)

        try:
            # Patch Path.exists to return True for the PDF check
            original_exists = Path.exists
            def fake_exists(self):
                if str(self).endswith(".pdf"):
                    return True
                return original_exists(self)

            with patch.object(Path, "exists", fake_exists):
                from gitcrumb.docker_export import export_pdf
                # Read the .marp.md before it's cleaned up
                read_marp = []

                original_write = Path.write_text
                def capture_write(self, content, *args, **kwargs):
                    if str(self).endswith(".marp.md"):
                        read_marp.append(content)
                    return original_write(self, content, *args, **kwargs)

                with patch.object(Path, "write_text", capture_write):
                    export_pdf(str(md_path))

            self.assertEqual(len(read_marp), 1)
            self.assertIn("marp: true", read_marp[0])
            self.assertIn("# Original", read_marp[0])
        finally:
            md_path.unlink()


if __name__ == "__main__":
    unittest.main()
