# $report_title

**Author**: $authors_displayed
**Date range**: $analysis_date_range
**Generated at**: $report_generated_at

---

## Executive Summary

- **Active repositories**: $repositories_count
- **Total commits**: $commits_count
- **Merge commits**: $merge_commits_count
- **Lines added**: $total_lines_added
- **Lines deleted**: $total_lines_deleted

---

<!-- #repo_block -->
## `$repository_name` — $repository_commits_count commits (+$repository_lines_added/-$repository_lines_deleted)

| Hash | Date | Message |
|------|-------|---------|
$repository_commit_rows
<!-- #/repo_block -->
