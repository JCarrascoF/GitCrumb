"""Internationalisation — English by default, set GITCRUMB_LANG=es for Spanish."""

from __future__ import annotations

from gitcrumb.locale import resolve_lang



_TRANSLATIONS: dict[str, dict[str, str]] = {
    # ── CLI description / help ───────────────────────────────
    "cli.description": "Git activity report over a time window.",
    "cli.path.help": "Root folder to scan (positional or --path).",
    "cli.non-interactive.help": "Do not prompt interactively (use defaults).",
    "cli.pdf.help": "Export Markdown report to PDF via Docker ({image}).",
    "cli.author.help": "Git author name or email. Repeatable for multiple authors.",
    "cli.start.help": "Start date YYYY-MM-DD (START_DATE).",
    "cli.end.help": "End date YYYY-MM-DD (END_DATE).",
    "cli.output.help": "Output file path (OUTPUT_FILE).",
    "cli.no-merges.help": "Exclude merge commits from the list (own code only).",
    "cli.debug.help": "Show breakdown by author and repo for debugging.",
    "cli.mark-merges.help": "Mark merge commits with (Merge) in the table.",

    # ── CLI runtime messages ─────────────────────────────────
    "cli.error.root_missing": "ERROR: Root folder does not exist: {path}",
    "cli.scanning": "Scanning: {path}",
    "cli.author_range": "Author(s): {authors} | Range: {start} → {end}",
    "cli.report_generated": "\nMarkdown report generated: {path}",
    "cli.summary.repos_commits": "Active repos: {repos} | Total commits: {commits}",
    "cli.summary.lines": "Lines added: {added} | Deleted: {deleted}",
    "cli.docker.unavailable": "\n⚠  Docker is not available. Install it at https://www.docker.com/products/docker-desktop",
    "cli.pdf.generated": "PDF generated: {path}",
    "cli.pdf.error": "\n⚠  Error generating the PDF.",
    "cli.cancelled": "\n\n⚠  Cancelled by user.",

    # ── Config interactive prompt ────────────────────────────
    "config.header": "\n⚙  Interactive configuration (Enter = accept default)\n",
    "config.label.root_dir": "Root folder to scan",
    "config.label.author": "Git author name or email",
    "config.label.start_date": "Start date YYYY-MM-DD",
    "config.label.end_date": "End date YYYY-MM-DD",

    # ── Report ───────────────────────────────────────────────
    "report.title": "Git Activity Report",
    "report.skipped": "\nUnchanged content (hash {h}), skipping write.",

    # ── Git parser debug ─────────────────────────────────────
    "git_parser.debug": "[{author}] {label}: {new_count} new ({dup_count} duplicates)",

    # ── Repo analyzer ────────────────────────────────────────
    "repo_analyzer.processing": "Processing: {name} ...",

    # ── Docker export ────────────────────────────────────────
    "docker.pulling": "Pulling image {image}...",
    "docker.pull_error": "Error downloading image: {err}",
    "docker.generating": "Generating PDF with Marp...",
    "docker.marp_error": "Marp error: {err}",

    # ── install.sh (not used in Python, kept for reference) ──
    "install.path_missing": "~/.local/bin is not in PATH.",
    "install.add_path": "Add it to your shell config (~/.zshrc, ~/.bash_profile):",
    "install.done": "gitcrumb installed → {target}",
    "install.try": "Try: gitcrumb --help",
}

_ES: dict[str, str] = {
    "cli.description": "Informe de actividad Git en ventana temporal.",
    "cli.path.help": "Carpeta raíz a escanear (posicional o --path).",
    "cli.non-interactive.help": "No pedir valores interactivamente (usa defaults).",
    "cli.pdf.help": "Exportar el informe Markdown a PDF vía Docker ({image}).",
    "cli.author.help": "Nombre o email del autor en Git. Repetible para varios autores.",
    "cli.start.help": "Fecha de inicio YYYY-MM-DD (START_DATE).",
    "cli.end.help": "Fecha de fin YYYY-MM-DD (END_DATE).",
    "cli.output.help": "Ruta del archivo de salida (OUTPUT_FILE).",
    "cli.no-merges.help": "Excluir merge commits del listado (solo código propio).",
    "cli.debug.help": "Mostrar desglose por autor y repo para depuración.",
    "cli.mark-merges.help": "Marcar merge commits con (Merge) en la tabla.",

    "cli.error.root_missing": "ERROR: La carpeta raíz no existe: {path}",
    "cli.scanning": "Escaneando: {path}",
    "cli.author_range": "Autor(es): {authors} | Rango: {start} → {end}",
    "cli.report_generated": "\nInforme Markdown generado: {path}",
    "cli.summary.repos_commits": "Repositorios activos: {repos} | Commits totales: {commits}",
    "cli.summary.lines": "Líneas añadidas: {added} | Eliminadas: {deleted}",
    "cli.docker.unavailable": "\n⚠  Docker no está disponible. Instálalo en https://www.docker.com/products/docker-desktop",
    "cli.pdf.generated": "PDF generado: {path}",
    "cli.pdf.error": "\n⚠  Error al generar el PDF.",
    "cli.cancelled": "\n\n⚠  Cancelado por el usuario.",

    "config.header": "\n⚙  Configuración interactiva (Enter = aceptar default)\n",
    "config.label.root_dir": "Carpeta raíz a escanear",
    "config.label.author": "Nombre o email del autor en Git",
    "config.label.start_date": "Fecha de inicio YYYY-MM-DD",
    "config.label.end_date": "Fecha de fin YYYY-MM-DD",

    "report.title": "Informe de Actividad Git",
    "report.skipped": "\nContenido sin cambios (hash {h}). Saltando escritura del MD.",

    "git_parser.debug": "[{author}] {label}: {new_count} nuevos ({dup_count} duplicados)",

    "repo_analyzer.processing": "Procesando: {name} ...",

    "docker.pulling": "Descargando imagen {image}...",
    "docker.pull_error": "Error al descargar la imagen: {err}",
    "docker.generating": "Generando PDF con Marp...",
    "docker.marp_error": "Error de Marp: {err}",

    "install.path_missing": "~/.local/bin no está en PATH.",
    "install.add_path": "Añádelo a tu shell config (~/.zshrc, ~/.bash_profile):",
    "install.done": "gitcrumb instalado → {target}",
    "install.try": "Prueba: gitcrumb --help",
}


def _lang() -> str:
    return resolve_lang()


def t(key: str, **kwargs: object) -> str:
    """Translate a message key. Falls back to English on missing keys."""
    translations = _TRANSLATIONS.copy()
    if _lang() == "es":
        translations.update(_ES)
    template = translations.get(key, _TRANSLATIONS.get(key, key))
    return template.format(**kwargs)
