"""Entry point — argparse and flow orchestration."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gitcrumb.config import resolve_config, _CLI_MAP
from gitcrumb.docker_export import MARP_IMAGE, check_docker, ensure_image, export_pdf
from gitcrumb.i18n import t
from gitcrumb.repo_analyzer import analyze_repositories
from gitcrumb.report import generate_report_md, write_report


def main() -> None:
    parser = argparse.ArgumentParser(
        description=t("cli.description"),
    )
    parser.add_argument(
        "path", nargs="?", default=None,
        help=t("cli.path.help"),
    )
    parser.add_argument(
        "--non-interactive", action="store_true",
        help=t("cli.non-interactive.help"),
    )
    parser.add_argument(
        "--pdf", action="store_true",
        help=t("cli.pdf.help", image=MARP_IMAGE),
    )
    parser.add_argument(
        "--author", dest="author", action="append",
        help=t("cli.author.help"),
    )
    parser.add_argument(
        "--start", dest="start",
        help=t("cli.start.help"),
    )
    parser.add_argument(
        "--end", dest="end",
        help=t("cli.end.help"),
    )
    parser.add_argument(
        "--output", dest="output",
        help=t("cli.output.help"),
    )
    parser.add_argument(
        "--no-merges", action="store_true",
        help=t("cli.no-merges.help"),
    )
    parser.add_argument(
        "--debug", action="store_true",
        help=t("cli.debug.help"),
    )
    parser.add_argument(
        "--mark-merges", action="store_true",
        help=t("cli.mark-merges.help"),
    )
    args = parser.parse_args()

    cli: dict[str, str] = {}
    for short_key, env_key in _CLI_MAP.items():
        val = getattr(args, short_key)
        if val is not None:
            cli[env_key] = val

    # Resolve configuration with precedence: CLI > interactive > default
    cfg = resolve_config(non_interactive=args.non_interactive, cli_args=cli)
    root_dir = cfg["ROOT_DIR"]

    # Combine authors (CLI list + config fallback) into a regex pattern for git
    author_list = args.author or [cfg.get("AUTHOR", "")]
    author_display = ", ".join(author_list)
    start_date = cfg["START_DATE"]
    end_date = cfg["END_DATE"]
    output_file = cfg["OUTPUT_FILE"]

    root_path = Path(root_dir).expanduser()
    if not root_path.is_dir():
        print(t("cli.error.root_missing", path=root_path), file=sys.stderr)
        sys.exit(1)

    # Ensure parent directory of output file exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    print(t("cli.scanning", path=root_path))
    print(t("cli.author_range", authors=author_display, start=start_date, end=end_date))

    results = analyze_repositories(
        root_dir, author_list, start_date, end_date,
        exclude_merges=args.no_merges, debug=args.debug,
    )

    content_body, new_hash = generate_report_md(
        results, author_display, start_date, end_date, str(root_path),
        mark_merges=args.mark_merges,
    )
    output_path = Path(output_file)
    write_report(output_path, content_body, new_hash)

    total_repos = len(results)
    total_commits = sum(r.total for r in results)
    total_added = sum(r.added for r in results)
    total_deleted = sum(r.deleted for r in results)

    print(t("cli.report_generated", path=output_file))
    print(t("cli.summary.repos_commits", repos=total_repos, commits=total_commits))
    print(t("cli.summary.lines", added=total_added, deleted=total_deleted))

    # Export to PDF if requested
    if args.pdf:
        if not check_docker():
            print(t("cli.docker.unavailable"))
            sys.exit(1)
        if not ensure_image(MARP_IMAGE):
            sys.exit(1)
        pdf_path = export_pdf(output_file)
        if pdf_path:
            print(t("cli.pdf.generated", path=pdf_path))
        else:
            print(t("cli.pdf.error"), file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(t("cli.cancelled"))
        sys.exit(0)
