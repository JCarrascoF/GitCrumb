# Arquitectura de gitcrumb

## Arquitectura general

Script plano sin dependencias externas (solo stdlib). Flujo lineal: **configuración → escaneo → extracción → generación → escritura**.

```
_gitcrumb_entry.py       # entry point → gitcrumb.cli:main()
gitcrumb/cli.py      # argparse + orquestación del flujo
gitcrumb/config.py   # prompt interactivo + resolución de configuración
gitcrumb/models.py   # dataclasses: Commit, RepoResult (con merge_hashes)
gitcrumb/git_parser.py       # subprocess → git log / git shortstat
gitcrumb/repo_analyzer.py    # find repos + analyze_repositories
gitcrumb/report.py           # generación Markdown desde template + hash
gitcrumb/docker_export.py    # Docker + Marp CLI (exportación PDF)
```

Archivos de plantilla:

```
gitcrumb/report_template.md  # template único: informe + bloque inline
TEMPLATE_REFERENCE.md   # documentación de variables disponibles
```

## Flujo de ejecución

```
cli.main()
 ├── argparse (--non-interactive, --pdf, --mark-merges, --debug, path, --author, --start, --end, --output, --no-merges)
 ├── config.resolve_config()        → dict[str, str]
 │    ├── CLI args                   # 1ª prioridad
 │    └── config.prompt_interactive() # 2ª: prompts con defaults editables
 ├── validar carpeta raíz + crear directorio de salida
 ├── repo_analyzer.analyze_repositories()
 │    ├── repo_analyzer.find_repos()          → list[Path]  (find .git recursivo)
 │    └── git_parser.extract_commits() × N    → list[Commit] por repo
 │    └── git_parser.extract_stats() × N      → (added, deleted) por repo
 ├── report.generate_report_md()              → str (Markdown completo)
 ├── report.write_report()                    → archivo .md (con hash de contenido)
 └── docker_export.export_pdf()?              → archivo .pdf (si --pdf y Docker disponible)
```

## Módulos

### `models.py` — Estructuras de datos

- **`Commit`**: hash corto, fecha `YYYY-MM-DD`, mensaje del commit.
- **`RepoResult`**: nombre relativo + lista de commits + stats (+/- líneas, merges) + `merge_hashes: set[str]`. Property `.total` para conteo.

Ambos inmutables por convención (sin setters). Se usan como DTOs puros entre funciones.

### `config.py` — Configuración

#### Prompt interactivo — `prompt_interactive()`

Solo se invoca si:
- No hay `--non-interactive`.
- `sys.stdin.isatty()` es `True` (no está en pipe).
- Ningún argumento CLI ha sido proporcionado.

Muestra cada campo con su default entre corchetes. Enter = aceptar default.

#### Resolución — `resolve_config()`

Precedencia estricta (primero gana):
1. **Argumentos CLI** (`path`, `--author`, `--start`, `--end`, `--output`).
2. **Prompt interactivo** o default.

Devuelve `dict[str, str]` con las claves configurables.

### `git_parser.py` — Parseo de terminal

Módulo dedicado a la ejecución de comandos git y parseo de su salida:

- `_parse_log()`: split por `|` (máx 2 cortes) → crea objetos `Commit`.
- `_git_log()`: ejecuta `subprocess.run(["git", "log", ...])` con filtros de autor, fechas y formato pipe-delimited.
- `extract_commits()`: una consulta por patrón de autor (evita regex OR de git). Deduplica por hash. Separa merges de no-merges vía `--no-merges` / `--merges`. Retorna `(commits, merge_count, merge_hashes)`. Con `debug=True` imprime desglose por autor.
- `extract_stats()`: ejecuta `git log --shortstat` y suma insertions/deletions con regex.

### `repo_analyzer.py` — Análisis de historial

Orquesta el escaneo de repositorios y la extracción de datos:

- `_find_git_root()`: `git rev-parse --show-toplevel` para encontrar el root de un repo.
- `_is_ignored_by_parent()`: `git check-ignore` desde el repo ancestro más cercano (respeta .gitignore).
- `find_repos()`: `rglob(".git")` recursivo, filtra por gitignore del ancestro.
- `analyze_repositories()`: itera repos encontrados → llama a `extract_commits()` + `extract_stats()` → retorna solo repos con commits en el rango.

### `report.py` — Generación Markdown desde template

Función pura: recibe datos, retorna string Markdown renderizado desde `report_template.md`. No hay flag `--template`; el template se aplica siempre.

#### Sistema de templates

Un solo fichero (`report_template.md`) contiene ambos niveles:
- **Template principal**: estructura del informe (encabezado, resumen ejecutivo, variables globales).
- **Repo block inline**: sección marcada con `<!-- #repo_block -->...<!-- #/repo_block -->` que define el formato por repositorio. Se coloca en la posición visual donde se expanden los bloques.

`_load_templates()` parsea el fichero:
1. Extrae el contenido entre los marcadores → template por repositorio.
2. Reemplaza la sección marcada con `$repositories_commit_analysis` → template principal.
3. Retorna `(Template_principal, repo_block_string)`.

#### Variables (self-explanatory)

Nivel informe: `$report_title`, `$authors_displayed`, `$analysis_date_range`, `$report_generated_at`, `$repositories_count`, `$commits_count`, `$merge_commits_count`, `$total_lines_added`, `$total_lines_deleted`, `$repositories_commit_analysis`.

Nivel repositorio: `$repository_name`, `$repository_commits_count`, `$repository_lines_added`, `$repository_lines_deleted`, `$repository_merge_commits_count`, `$repository_commit_rows`.

Ver [TEMPLATE_REFERENCE.md](../TEMPLATE_REFERENCE.md) para la referencia completa.

#### Hash de contenido

Incluye hash SHA-256 embebido en comentario HTML (`<!-- gitcrumb-hash: ... -->`) al final del archivo. Si el hash coincide con una ejecución anterior, se salta la reescritura.

### Gestión de merge commits

El sistema hace dos pasadas por autor (`git log --no-merges` + `git log --merges`) para distinguir commits propios de merges. El comportamiento depende de flags:

- **Sin flags** (por defecto): la tabla solo muestra no-merges.
- Con `--no-merges`: los merges se excluyen completamente del resultado — ni en tabla ni en contadores.
- Con `--mark-merges`: los merges aparecen en la tabla marcados con `(Merge)` junto al hash.

### Múltiples autores

Cada patrón de autor (`--author`) genera una consulta `git log --no-merges` + `git log --merges` independiente. Los resultados se deduplican por hash corto. Un mismo commit puede aparecer en ambas consultas si el author y committer difieren (ej. PR merge donde el autor del cambio no es quien hizo el merge).

### `docker_export.py` — Exportación PDF

- `check_docker()`: ejecuta `docker info` y retorna `True/False`.
- `ensure_image()`: inspecciona/pull de la imagen Marp si no existe localmente.
- `export_pdf()`: monta el directorio en un contenedor `marpteam/marp-cli`, genera PDF A4 con frontmatter YAML.

Dependencia opcional: Docker Desktop. Sin Docker, el script funciona normalmente (solo `.md`).

### `cli.py` — Punto de entrada

Orquesta el flujo completo importando los módulos anteriores. Maneja validación inicial, escritura del archivo final y exportación PDF opcional (`--pdf`).

## Extensión: nuevos formatos de salida

Para agregar CSV o JSON:

1. Crear función en `report.py` (o nuevo módulo) siguiendo la firma de `generate_report_md()`.
2. Llamarla desde `cli.main()` y escribir a un archivo con extensión adecuada.
3. Opcional: añadir argumento CLI para seleccionar formato dinámicamente.
