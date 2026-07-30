# gitcrumb — Referencia de plantillas (templates)

El fichero `gitcrumb/report_template.md` define el formato completo del informe generado.
Se aplica automáticamente en cada ejecución. Puedes modificarlo directamente
para personalizar el aspecto del informe.

## Estructura del archivo

Todo está en un solo fichero (`gitcrumb/report_template.md`). El template por repositorio
se define inline entre marcadores especiales, en la posición donde se expandirán
los bloques de cada repositorio:

```markdown
...informe principal...

<!-- #repo_block -->
## `$repository_name` — $repository_commits_count commits (+$repository_lines_added/-$repository_lines_deleted)

| Hash | Fecha | Mensaje |
|------|-------|---------|
$repository_commit_rows
<!-- #/repo_block -->
```

Los marcadores `<!-- #repo_block -->` y `<!-- #/repo_block -->` se extraen automáticamente
y no aparecen en el informe final. El contenido entre ellos define el formato de cada repositorio.

## Variables disponibles (nivel informe)

| Variable | Descripción | Ejemplo |
|---|---|---|
| `$report_title` | Título del documento | Informe de Actividad Git |
| `$authors_displayed` | Autor(es) filtrados en el informe | your@email.com, JaneDoe |
| `$analysis_date_range` | Rango de fechas analizado | 2026-01-01 → 2026-07-27 |
| `$report_generated_at` | Fecha y hora de generación | 2026-07-29 10:55:51 +0200 |
| `$repositories_count` | Repositorios con actividad | 26 |
| `$commits_count` | Commits propios (sin merges) | 423 |
| `$merge_commits_count` | Merge commits | 126 |
| `$total_lines_added` | Líneas añadidas en total | 145670 |
| `$total_lines_deleted` | Líneas eliminadas en total | 209854 |
| `$repositories_commit_analysis` | Bloque con actividad por repositorio (generado automáticamente) | — |

## Variables disponibles (nivel repositorio)

Usables dentro de la sección `<!-- #repo_block -->`:

| Variable | Descripción | Ejemplo |
|---|---|---|
| `$repository_name` | Ruta relativa del repositorio | backend/api-service |
| `$repository_commits_count` | Número de commits en este repo | 42 |
| `$repository_lines_added` | Líneas añadidas en este repo | 3450 |
| `$repository_lines_deleted` | Líneas eliminadas en este repo | 1280 |
| `$repository_merge_commits_count` | Merge commits en este repo | 5 |
| `$repository_commit_rows` | Filas de la tabla de commits (generado automáticamente) | — |

## Notas

- Se usa la sintaxis de `string.Template` de Python: `$nombre` o `${nombre}`.
- Para incluir un signo `$` literal en el resultado, usa `$$`.
