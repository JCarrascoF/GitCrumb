"""Punto de entrada — argparse y orquestación del flujo."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gitrack.config import resolve_config, _CLI_MAP
from gitrack.docker_export import MARP_IMAGE, check_docker, ensure_image, export_pdf
from gitrack.repo_analyzer import analyze_repositories
from gitrack.report import generate_report_md, write_report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Informe de actividad Git en ventana temporal.",
    )
    parser.add_argument(
        "path", nargs="?", default=None,
        help="Carpeta raíz a escanear (posicional o --path).",
    )
    parser.add_argument(
        "--non-interactive", action="store_true",
        help="No pedir valores interactivamente (usa defaults).",
    )
    parser.add_argument(
        "--pdf", action="store_true",
        help=f"Exportar el informe Markdown a PDF vía Docker ({MARP_IMAGE}).",
    )
    parser.add_argument(
        "--author", dest="author", action="append",
        help="Nombre o email del autor en Git. Repetible para varios autores.",
    )
    parser.add_argument(
        "--start", dest="start",
        help="Fecha de inicio YYYY-MM-DD (START_DATE).",
    )
    parser.add_argument(
        "--end", dest="end",
        help="Fecha de fin YYYY-MM-DD (END_DATE).",
    )
    parser.add_argument(
        "--output", dest="output",
        help="Ruta del archivo de salida (OUTPUT_FILE).",
    )
    parser.add_argument(
        "--no-merges", action="store_true",
        help="Excluir merge commits del listado (solo código propio).",
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Mostrar desglose por autor y repo para depuración.",
    )
    parser.add_argument(
        "--mark-merges", action="store_true",
        help="Marcar merge commits con (Merge) en la tabla.",
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
        print(f"ERROR: La carpeta raíz no existe: {root_path}", file=sys.stderr)
        sys.exit(1)

    # Ensure parent directory of output file exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    print(f"Iniciando escaneo en: {root_path}")
    print(f"Autor(es): {author_display} | Rango: {start_date} → {end_date}\n")

    results = analyze_repositories(
        root_dir, author_list, start_date, end_date,
        exclude_merges=args.no_merges, debug=args.debug,
    )

    content_body, new_hash = generate_report_md(
        results, author_display, start_date, end_date, str(root_path),
        mark_merges=args.mark_merges,
    )
    output_path = Path(output_file)
    written = write_report(output_path, content_body, new_hash)

    total_repos = len(results)
    total_commits = sum(r.total for r in results)
    total_added = sum(r.added for r in results)
    total_deleted = sum(r.deleted for r in results)

    print(f"\nInforme Markdown generado: {output_file}")
    print(f"Repositorios activos: {total_repos} | Commits totales: {total_commits}")
    print(f"Líneas añadidas: {total_added} | Eliminadas: {total_deleted}")

    # Export to PDF if requested
    if args.pdf:
        if not check_docker():
            print("\n⚠  Docker no está disponible. Instálalo en https://www.docker.com/products/docker-desktop")
            sys.exit(1)
        if not ensure_image(MARP_IMAGE):
            sys.exit(1)
        pdf_path = export_pdf(output_file)
        if pdf_path:
            print(f"PDF generado: {pdf_path}")
        else:
            print("\n⚠  Error al generar el PDF.", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠  Cancelado por el usuario.")
        sys.exit(0)
