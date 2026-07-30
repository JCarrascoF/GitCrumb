# gitcrumb Architecture

## Overall architecture

Flat script with no external dependencies (stdlib only). Linear flow: **configuration → scanning → extraction → generation → writing**.

```
_gitcrumb_entry.py       # entry point → gitcrumb.cli:main()
gitcrumb/cli.py      # argparse + flow orchestration
gitcrumb/config.py   # interactive prompt + configuration resolution
gitcrumb/models.py   # dataclasses: Commit, RepoResult (with merge_hashes)
gitcrumb/git_parser.py       # subprocess → git log / git shortstat
gitcrumb/repo_analyzer.py    # find repos + analyze_repositories
gitcrumb/report.py           # Markdown generation from template + hash
gitcrumb/docker_export.py    # Docker + Marp CLI (PDF export)
```

Template files:

```
gitcrumb/report_template.md  # single template: report + inline block
TEMPLATE_REFERENCE.md   # documentation of available variables
```

## Execution flow

```
cli.main()
 ├── argparse (--non-interactive, --pdf, --mark-merges, --debug, path, --author, --start, --end, --output, --no-merges)
 ├── config.resolve_config()        → dict[str, str]
 │    ├── CLI args                   # 1st priority
 │    └── config.prompt_interactive() # 2nd: prompts with editable defaults
 ├── validate root folder + create output directory
 ├── repo_analyzer.analyze_repositories()
 │    ├── repo_analyzer.find_repos()          → list[Path]  (recursive .git search)
 │    └── git_parser.extract_commits() × N    → list[Commit] per repo
 │    └── git_parser.extract_stats() × N      → (added, deleted) per repo
 ├── report.generate_report_md()              → str (full Markdown)
 ├── report.write_report()                    → .md file (with content hash)
 └── docker_export.export_pdf()?              → .pdf file (if --pdf and Docker available)
```

## Modules

### `models.py` — Data structures

- **`Commit`**: short hash, date `YYYY-MM-DD`, commit message.
- **`RepoResult`**: relative name + list of commits + stats (+/- lines, merges) + `merge_hashes: set[str]`. Property `.total` for count.

Both immutable by convention (no setters). Used as pure DTOs between functions.

### `config.py` — Configuration

#### Interactive prompt — `prompt_interactive()`

Only invoked if:
- No `--non-interactive`.
- `sys.stdin.isatty()` is `True` (not in a pipe).
- No CLI arguments provided.

Shows each field with its default in brackets. Enter = accept default.

#### Resolution — `resolve_config()`

Strict precedence (first wins):
1. **CLI arguments** (`path`, `--author`, `--start`, `--end`, `--output`).
2. **Interactive prompt** or default.

Returns `dict[str, str]` with configurable keys.

### `git_parser.py` — Terminal parsing

Module dedicated to running git commands and parsing their output:

- `_parse_log()`: split by `|` (max 2 cuts) → creates `Commit` objects.
- `_git_log()`: runs `subprocess.run(["git", "log", ...])` with author, date filters and pipe-delimited format.
- `extract_commits()`: one query per author pattern (avoids git regex OR). Deduplicates by hash. Separates merges from non-merges via `--no-merges` / `--merges`. Returns `(commits, merge_count, merge_hashes)`. With `debug=True` prints breakdown by author.
- `extract_stats()`: runs `git log --shortstat` and sums insertions/deletions with regex.

### `repo_analyzer.py` — History analysis

Orchestrates repository scanning and data extraction:

- `_find_git_root()`: `git rev-parse --show-toplevel` to find a repo's root.
- `_is_ignored_by_parent()`: `git check-ignore` from the nearest ancestor repo (respects .gitignore).
- `find_repos()`: recursive `rglob(".git")`, filters by ancestor's gitignore.
- `analyze_repositories()`: iterates found repos → calls `extract_commits()` + `extract_stats()` → returns only repos with commits in the range.

### `report.py` — Markdown generation from template

Pure function: receives data, returns rendered Markdown string from `report_template.md`. There is no `--template` flag; the template always applies.

#### Template system

A single file (`report_template.md`) contains both levels:
- **Main template**: report structure (header, executive summary, global variables).
- **Inline repo block**: section marked with `<!-- #repo_block -->...<!-- #/repo_block -->` that defines per-repository format. Placed at the visual position where blocks expand.

`_load_templates()` parses the file:
1. Extracts content between markers → repository template.
2. Replaces the marked section with `$repositories_commit_analysis` → main template.
3. Returns `(main_template, repo_block_string)`.

#### Variables (self-explanatory)

Report level: `$report_title`, `$authors_displayed`, `$analysis_date_range`, `$report_generated_at`, `$repositories_count`, `$commits_count`, `$merge_commits_count`, `$total_lines_added`, `$total_lines_deleted`, `$repositories_commit_analysis`.

Repository level: `$repository_name`, `$repository_commits_count`, `$repository_lines_added`, `$repository_lines_deleted`, `$repository_merge_commits_count`, `$repository_commit_rows`.

See [TEMPLATE_REFERENCE.md](../TEMPLATE_REFERENCE.en.md) for the full reference.

#### Content hash

Includes SHA-256 hash embedded in an HTML comment (`<!-- gitcrumb-hash: ... -->`) at the end of the file. If the hash matches a previous run, skips rewrite.

### Merge commit handling

The system makes two passes per author (`git log --no-merges` + `git log --merges`) to distinguish own commits from merges. Behavior depends on flags:

- **No flags** (default): table shows only non-merges.
- With `--no-merges`: merges are completely excluded — not in table nor counters.
- With `--mark-merges`: merges appear in the table marked with `(Merge)` next to the hash.

### Multiple authors

Each author pattern (`--author`) generates an independent `git log --no-merges` + `git log --merges` query. Results are deduplicated by short hash. The same commit can appear in both queries if author and committer differ (e.g., PR merge where the change's author is not who performed the merge).

### `docker_export.py` — PDF export

- `check_docker()`: runs `docker info`, returns `True/False`.
- `ensure_image()`: inspects/pulls Marp image if it doesn't exist locally.
- `export_pdf()`: mounts directory in a `marpteam/marp-cli` container, generates A4 PDF with YAML frontmatter.

Optional dependency: Docker Desktop. Without Docker, the script works normally (`.md` only).

### `cli.py` — Entry point

Orchestrates the full flow importing the modules above. Handles initial validation, final file writing, and optional PDF export (`--pdf`).

## Extension: new output formats

To add CSV or JSON:

1. Create a function in `report.py` (or a new module) following the signature of `generate_report_md()`.
2. Call it from `cli.main()` and write to a file with the appropriate extension.
3. Optional: add a CLI argument to select format dynamically.
