"""Interactive prompt and configuration resolution."""

from __future__ import annotations

import os
import sys
from pathlib import Path


# =============================================================================
# 1. INTERACTIVE PROMPT WITH DEFAULTS
# =============================================================================

_DEFAULT_KEYS = [
    ("ROOT_DIR", "Carpeta raíz a escanear", lambda: os.path.expanduser("~/Desarrollo")),
    ("AUTHOR", "Nombre o email del autor en Git", "your@email.com"),
    ("START_DATE", "Fecha de inicio (YYYY-MM-DD)", "2026-01-01"),
    ("END_DATE", "Fecha de fin (YYYY-MM-DD)", "2026-07-27"),
]


def _default_output(root_dir: str, start_date: str, end_date: str) -> str:
    """Build the default output path from the scanned directory and date range."""
    base = Path(root_dir).expanduser()
    return str(base / f"git_report_{start_date}_{end_date}.md")


def prompt_interactive(cli_args: dict[str, str]) -> dict[str, str]:
    """Prompt the user for values with editable defaults.

    Only asks for fields not already in *cli_args*.
    Press Enter to accept the default value (shown in brackets).
    Ctrl+C cancels execution cleanly.
    """
    pending = [(k, e, d) for k, e, d in _DEFAULT_KEYS if k not in cli_args]
    if not pending:
        return {}

    print("\n⚙  Configuración interactiva (Enter = aceptar default)\n")
    result: dict[str, str] = {}
    for key, label, default in pending:
        if callable(default):
            default = default()
        prompt = f"  {label} [{default}]: "
        try:
            value = input(prompt).strip()
        except KeyboardInterrupt:
            print("\n\n⚠  Cancelado por el usuario.")
            sys.exit(0)
        result[key] = value if value else str(default)
    print()
    return result


# =============================================================================
# 2. CONFIGURATION RESOLUTION
# =============================================================================

_CLI_MAP: dict[str, str] = {
    "path": "ROOT_DIR",
    "author": "AUTHOR",
    "start": "START_DATE",
    "end": "END_DATE",
    "output": "OUTPUT_FILE",
}


def resolve_config(
    non_interactive: bool = False,
    cli_args: dict[str, str] | None = None,
) -> dict[str, str]:
    """Determine the final configuration values.

    Precedence:
      1. CLI arguments (--path, --author, --start, --end, --output)
      2. Interactive prompt (only if TTY and not --non-interactive)
      3. Default values
    """
    cli_args = cli_args or {}
    config: dict[str, str] = {}

    for key, _label, default in _DEFAULT_KEYS:
        # 1) CLI argument
        if key in cli_args:
            config[key] = cli_args[key]
            continue

        # 2) Interactive or default
        if not non_interactive and sys.stdin.isatty():
            interactive = prompt_interactive(cli_args)
            config.update(interactive)
            break
        else:
            config[key] = str(default()) if callable(default) else default

    # Apply any CLI values that are outside _DEFAULT_KEYS (e.g. OUTPUT_FILE / --output)
    for key in cli_args:
        if key not in config:
            config[key] = cli_args[key]

    # Derive OUTPUT_FILE from ROOT_DIR + START_DATE + END_DATE when not provided
    if "OUTPUT_FILE" not in config:
        config["OUTPUT_FILE"] = _default_output(
            config.get("ROOT_DIR", os.path.expanduser("~/Desarrollo")),
            config.get("START_DATE", "2026-01-01"),
            config.get("END_DATE", "2026-07-27"),
        )
    return config
