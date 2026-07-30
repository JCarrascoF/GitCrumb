# gitcrumb — Template Reference

The file `gitcrumb/report_template.md` defines the full format of the generated report.
It is automatically applied on each run. You can modify it directly
to customize the appearance of the report.

## File structure

Everything is in a single file (`gitcrumb/report_template.md`). The per-repository template
is defined inline between special markers, at the position where each repository's blocks will expand:

```markdown
...main report...

<!-- #repo_block -->
## `$repository_name` — $repository_commits_count commits (+$repository_lines_added/-$repository_lines_deleted)

| Hash | Date | Message |
|------|-------|---------|
$repository_commit_rows
<!-- #/repo_block -->
```

The markers `<!-- #repo_block -->` and `<!-- #/repo_block -->` are automatically extracted
and do not appear in the final report. The content between them defines each repository's format.

## Available variables (report level)

| Variable | Description | Example |
|---|---|---|
| `$report_title` | Document title | Git Activity Report — Employment Period |
| `$authors_displayed` | Author(s) filtered in the report | your@email.com, JaneDoe |
| `$analysis_date_range` | Analyzed date range | 2026-01-01 → 2026-07-27 |
| `$report_generated_at` | Generation date and time | 2026-07-29 10:55:51 +0200 |
| `$repositories_count` | Repositories with activity | 26 |
| `$commits_count` | Own commits (excluding merges) | 423 |
| `$merge_commits_count` | Merge commits | 126 |
| `$total_lines_added` | Total lines added | 145670 |
| `$total_lines_deleted` | Total lines deleted | 209854 |
| `$repositories_commit_analysis` | Per-repository activity block (auto-generated) | — |

## Available variables (repository level)

Usable within the `<!-- #repo_block -->` section:

| Variable | Description | Example |
|---|---|---|
| `$repository_name` | Relative path of the repository | backend/api-service |
| `$repository_commits_count` | Number of commits in this repo | 42 |
| `$repository_lines_added` | Lines added in this repo | 3450 |
| `$repository_lines_deleted` | Lines deleted in this repo | 1280 |
| `$repository_merge_commits_count` | Merge commits in this repo | 5 |
| `$repository_commit_rows` | Commit table rows (auto-generated) | — |

## Notes

- Uses Python's `string.Template` syntax: `$name` or `${name}`.
- To include a literal `$` in the output, use `$$`.
