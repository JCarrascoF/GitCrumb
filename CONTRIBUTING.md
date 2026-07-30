# Contributing to GitCrumb

Thank you for your interest in contributing! This document describes how to get involved.

## Prerequisites

- Python 3.10+
- Git installed

## Local development

```bash
git clone git@github.com:<user>/gitcrumb.git
cd gitcrumb
./install.sh
```

## Running tests

```bash
python -m pytest tests/ -v
```

## Submitting changes

1. Create a branch from `main`.
2. Make your changes following the existing code style.
3. Add or update tests as appropriate.
4. Run `pytest` to verify everything passes.
5. Open a Pull Request describing your changes.

## Code guidelines

- **Stdlib only**: no external dependencies allowed.
- **Python 3.10+**: use type hints and modern language features.
- **No unnecessary abstractions**: keep code simple and direct.
- **Tests required**: every change must be covered by tests.

## Reporting an issue

Use [GitHub Issues](https://github.com/<user>/gitcrumb/issues) to report bugs or request improvements. Include:

1. GitCrumb version used.
2. Operating system and Python version.
3. Steps to reproduce the issue.
4. Expected vs. actual behavior.
