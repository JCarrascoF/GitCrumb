# GitCrumb

Generates a Git activity report from commit history within a time window. Recursively scans a root folder, extracts commits by author, and produces a **Markdown** file with formal structure: header, per-repository tables, and an executive summary. Optionally exports to **PDF**.

## Requirements

- Python 3.10+ (stdlib only, zero external dependencies)
- Git installed on the system
- macOS / Linux compatible
- *(Optional)* **Docker** for PDF export (uses the `marpteam/marp-cli` image)

## Installation

### After cloning

```bash
git clone git@github.com:<user>/gitcrumb.git
cd gitcrumb
./install.sh              # creates a global "gitcrumb" alias
```

The script checks that `~/.local/bin` is in your PATH and creates an automatic symlink.

### Manual (without install.sh)

```bash
ln -sf $(pwd)/_gitcrumb_entry.py ~/.local/bin/gitcrumb
```

## Quick usage

```bash
# Interactive mode → generates .md report
gitcrumb

# Path as positional argument + CLI parameters
gitcrumb ~/Dev --author "your@email.com" --start 2026-01-01 --end 2026-07-27

# With PDF export (requires Docker)
gitcrumb ~/Dev --pdf

# Non-interactive (uses defaults) — useful in CI / scripts
gitcrumb --non-interactive

# Multiple authors + exclude merges from the table
gitcrumb ~/Dev --author "your@email.com" --author "JaneDoe" --no-merges

# Mark merge commits with (Merge) in the table
gitcrumb ~/Dev --mark-merges

# Debug: breakdown by author and repo
gitcrumb ~/Dev --debug
```

## Configuration

Parameters are passed as CLI arguments. If not provided, the script asks interactively (or uses defaults with `--non-interactive`).

| Argument | Description | Default value |
|---|---|---|
| `--path` | Directory to scan recursively | `$HOME/Desarrollo` |
| `--author` | Git author name or email (repeatable) | `your@email.com` |
| `--start` | Start date (inclusive) | `2026-01-01` |
| `--end` | End date (inclusive) | `2026-07-27` |
| `--output` | Output `.md` file path | `{ROOT_DIR}/git_report_{START}_{END}.md` |
| `--no-merges` | Exclude merge commits from the table | — |
| `--mark-merges` | Include merges in the table marked with `(Merge)` | — |
| `--debug` | Show breakdown by author and repo (duplicates, counts) | — |

## Generated report structure (Markdown)

The format is defined in `gitcrumb/report_template.md` and can be customized by editing that file:

```markdown
# Git Activity Report — Employment Period

**Author**: your@email.com
**Date range**: 2025-01-01 → 2025-12-31
**Generated at**: 2025-12-31 14:30:00 +0100

---

## Executive Summary

- **Active repositories**: 3
- **Total commits**: 87
- **Lines added**: 12345
- **Lines deleted**: 6789

---

## `proyecto-alpha` — 40 commits (+1234/-567)

| Hash | Date | Message |
|------|-------|---------|
| `a1b2c3d` | 2025-03-15 | Fix login timeout |
| `e4f5a6b` | 2025-03-16 | Add user validation |
```

## PDF Export

```bash
gitcrumb --pdf   # requires Docker (uses marpteam/marp-cli image)
```

Generates a `.pdf` file with the same name as the Markdown one, in the same location. The conversion runs inside a Docker container — nothing is installed on the host.

## Execution flow

1. **Configuration** — Resolves parameters (CLI → interactive → default).
2. **Validation** — Checks root folder exists and creates output directory if needed.
3. **Scanning** — Recursively searches all `.git` directories within `--path`, respecting the nearest ancestor repository's `.gitignore`.
4. **Extraction** — Runs `git log` per repository, filtering by author and date range. One query per author (avoids regex OR) and two passes (`--no-merges` + `--merges`) to distinguish own commits from merges.
5. **Filtering** — Only includes repositories with commits in the period.
6. **Generation** — Builds Markdown from `gitcrumb/report_template.md` with header, executive summary, and per-repo tables (sorted alphabetically).
7. **Writing** — Saves `.md` to `--output`. If content hasn't changed since a previous run (verified by SHA-256 hash), skips rewrite.
8. **PDF Export** *(optional)* — Converts to PDF via Docker + Marp if `--pdf` is passed.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.en.md) for internal flow and architecture details.
