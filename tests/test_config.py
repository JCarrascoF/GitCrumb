"""Tests para config.py — resolución de configuración."""

import unittest
from pathlib import Path
from unittest.mock import patch

from gitrack.config import _default_output, resolve_config


class TestDefaultOutput(unittest.TestCase):
    def test_builds_path(self):
        result = _default_output("/home/user/Dev", "2025-01-01", "2025-12-31")
        self.assertEqual(result, "/home/user/Dev/git_report_2025-01-01_2025-12-31.md")

    def test_expands_tilde(self):
        result = _default_output("~/Dev", "2026-01-01", "2026-07-27")
        home = Path.home()
        self.assertTrue(result.startswith(str(home)))


class TestResolveConfig(unittest.TestCase):

    def test_cli_args_take_precedence(self):
        with patch("gitrack.config.sys.stdin.isatty", return_value=False):
            cfg = resolve_config(
                non_interactive=True,
                cli_args={
                    "ROOT_DIR": "/custom/path",
                    "START_DATE": "2024-01-01",
                    "END_DATE": "2024-06-30",
                },
            )
        self.assertEqual(cfg["ROOT_DIR"], "/custom/path")
        self.assertEqual(cfg["START_DATE"], "2024-01-01")
        self.assertEqual(cfg["END_DATE"], "2024-06-30")

    def test_defaults_when_no_args(self):
        with patch("gitrack.config.sys.stdin.isatty", return_value=False):
            cfg = resolve_config(non_interactive=True, cli_args={})
        self.assertIn("ROOT_DIR", cfg)
        self.assertIn("START_DATE", cfg)
        self.assertIn("END_DATE", cfg)
        self.assertIn("OUTPUT_FILE", cfg)

    def test_output_file_derived(self):
        with patch("gitrack.config.sys.stdin.isatty", return_value=False):
            cfg = resolve_config(
                non_interactive=True,
                cli_args={
                    "ROOT_DIR": "/tmp/test",
                    "START_DATE": "2025-06-01",
                    "END_DATE": "2025-06-30",
                },
            )
        self.assertEqual(cfg["OUTPUT_FILE"], "/tmp/test/git_report_2025-06-01_2025-06-30.md")

    def test_output_file_cli_overrides_derived(self):
        with patch("gitrack.config.sys.stdin.isatty", return_value=False):
            cfg = resolve_config(
                non_interactive=True,
                cli_args={
                    "ROOT_DIR": "/tmp/test",
                    "START_DATE": "2025-01-01",
                    "END_DATE": "2025-12-31",
                    "OUTPUT_FILE": "/custom/output.md",
                },
            )
        self.assertEqual(cfg["OUTPUT_FILE"], "/custom/output.md")

    def test_author_default(self):
        with patch("gitrack.config.sys.stdin.isatty", return_value=False):
            cfg = resolve_config(non_interactive=True, cli_args={})
        self.assertEqual(cfg["AUTHOR"], "your@email.com")


if __name__ == "__main__":
    unittest.main()
