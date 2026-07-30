"""Tests for gitcrumb.locale — XDG config file + precedence."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from gitcrumb.locale import read_lang_from_config, resolve_lang


class TestReadLangFromConfig(unittest.TestCase):
    """read_lang_from_config parses ~/.config/gitcrumb/config."""

    def test_returns_none_when_missing(self):
        with patch.object(Path, "home", return_value=Path("/tmp/nonexistent")):
            self.assertIsNone(read_lang_from_config())

    def test_parses_es(self):
        tmp = Path(__file__).parent / ".test_locale"
        tmp.mkdir(exist_ok=True)
        cfg = tmp / "config"
        cfg.write_text("lang = es\n", encoding="utf-8")

        with patch.object(Path, "home", return_value=tmp.parent / ".test"):
            # Repoint XDG to our test dir
            with patch("gitcrumb.locale._XDG_CONFIG", cfg):
                self.assertEqual(read_lang_from_config(), "es")

        cfg.unlink()
        tmp.rmdir()

    def test_parses_en(self):
        tmp = Path(__file__).parent / ".test_locale"
        tmp.mkdir(exist_ok=True)
        cfg = tmp / "config"
        cfg.write_text("lang = en\n", encoding="utf-8")

        with patch.object(Path, "home", return_value=tmp.parent / ".test"):
            with patch("gitcrumb.locale._XDG_CONFIG", cfg):
                self.assertEqual(read_lang_from_config(), "en")

        cfg.unlink()
        tmp.rmdir()

    def test_ignores_comments_and_blank_lines(self):
        tmp = Path(__file__).parent / ".test_locale"
        tmp.mkdir(exist_ok=True)
        cfg = tmp / "config"
        cfg.write_text("# comment\n\nlang = es\n", encoding="utf-8")

        with patch("gitcrumb.locale._XDG_CONFIG", cfg):
            self.assertEqual(read_lang_from_config(), "es")

        cfg.unlink()
        tmp.rmdir()


class TestResolveLang(unittest.TestCase):
    """resolve_lang applies precedence: CLI > config > env > default."""

    def test_default_is_en(self):
        with patch("gitcrumb.locale.read_lang_from_config", return_value=None), \
             patch.dict(os.environ, {}, clear=True):
            self.assertEqual(resolve_lang(), "en")

    def test_cli_wins_over_all(self):
        with patch("gitcrumb.locale.read_lang_from_config", return_value="es"), \
             patch.dict(os.environ, {"GITCRUMB_LANG": "en"}, clear=True):
            self.assertEqual(resolve_lang(cli_lang="es"), "es")
            self.assertEqual(resolve_lang(cli_lang="en"), "en")

    def test_env_wins_over_default(self):
        with patch("gitcrumb.locale.read_lang_from_config", return_value=None), \
             patch.dict(os.environ, {"GITCRUMB_LANG": "es"}, clear=True):
            self.assertEqual(resolve_lang(), "es")

    def test_config_wins_over_env(self):
        with patch("gitcrumb.locale.read_lang_from_config", return_value="en"), \
             patch.dict(os.environ, {"GITCRUMB_LANG": "es"}, clear=True):
            self.assertEqual(resolve_lang(), "en")


if __name__ == "__main__":
    unittest.main()
