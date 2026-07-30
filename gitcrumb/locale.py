"""Locale configuration — reads ~/.config/gitcrumb/config (XDG pattern).

Precedence: CLI flag > config file > GITCRUMB_LANG env var > default (en).
"""

from __future__ import annotations

import os
from pathlib import Path

_XDG_CONFIG = Path.home() / ".config" / "gitcrumb" / "config"


def read_lang_from_config() -> str | None:
    """Read 'lang' from the XDG config file, or None if not set."""
    try:
        text = _XDG_CONFIG.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, _, value = stripped.partition("=")
        if key.strip().lower() == "lang":
            val = value.strip()
            return val if val else None

    return None


def resolve_lang(cli_lang: str | None = None) -> str:
    """Return the active language code.

    Precedence: CLI flag > config file > env var > default (en).
    """
    if cli_lang is not None and cli_lang:
        return "es" if cli_lang == "es" else "en"
    cfg = read_lang_from_config()
    if cfg is not None:
        return "es" if cfg == "es" else "en"
    env = os.environ.get("GITCRUMB_LANG", "")
    if env:
        return "es" if env == "es" else "en"
    return "en"
