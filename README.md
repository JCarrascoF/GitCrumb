[English](README.en.md)

# GitCrumb

Genera un informe de actividad Git a partir del historial de commits en una ventana temporal. Escanea recursivamente una carpeta raíz, extrae los commits por autor y produce un archivo **Markdown** con estructura formal: encabezado, tablas por repositorio y resumen ejecutivo. Opcionalmente exporta a **PDF**.

## Requisitos

- Python 3.10+ (solo stdlib, cero dependencias externas)
- Git instalado en el sistema
- macOS / Linux compatible
- *(Opcional)* **Docker** para exportar a PDF (usa la imagen `marpteam/marp-cli`)

## Instalación

### Post-clonación

```bash
git clone git@github.com:<user>/gitcrumb.git
cd gitcrumb
./install.sh              # crea el alias global "gitcrumb"
```

El script verifica que `~/.local/bin` esté en PATH y crea un symlink automático.

### Manual (sin install.sh)

```bash
ln -sf $(pwd)/_gitcrumb_entry.py ~/.local/bin/gitcrumb
```

## Uso rápido

```bash
# Modo interactivo → genera informe .md
gitcrumb

# Path como argumento posicional + parámetros CLI
gitcrumb ~/Dev --author "your@email.com" --start 2026-01-01 --end 2026-07-27

# Con exportación a PDF (requiere Docker)
gitcrumb ~/Dev --pdf

# Sin prompts (usa defaults) — útil en CI / scripts
gitcrumb --non-interactive

# Múltiples autores + excluir merges de la tabla
gitcrumb ~/Dev --author "your@email.com" --author "JaneDoe" --no-merges

# Marcar merge commits con (Merge) en la tabla
gitcrumb ~/Dev --mark-merges

# Depuración: desglose por autor y repo
gitcrumb ~/Dev --debug
```

## Configuración

Los parámetros se pasan como argumentos CLI. Si no se indican, el script pregunta interactivamente (o usa defaults con `--non-interactive`).

| Argumento | Descripción | Valor por defecto |
|---|---|---|
| `--path` | Directorio a escanear recursivamente | `$HOME/Desarrollo` |
| `--author` | Nombre o email del autor en Git (repetible) | `your@email.com` |
| `--start` | Fecha de inicio (inclusive) | `2026-01-01` |
| `--end` | Fecha de fin (inclusive) | `2026-07-27` |
| `--output` | Ruta del archivo `.md` resultante | `{ROOT_DIR}/git_report_{START}_{END}.md` |
| `--no-merges` | Excluir merge commits de la tabla | — |
| `--mark-merges` | Incluir merges en la tabla marcados con `(Merge)` | — |
| `--debug` | Mostrar desglose por autor y repo (duplicados, conteos) | — |

## Estructura del informe generado (Markdown)

El formato se define en `gitcrumb/report_template.md` y puede personalizarse editando ese fichero:

```markdown
# Informe de Actividad Git

**Autor**: your@email.com
**Rango de fechas**: 2025-01-01 → 2025-12-31
**Generado el**: 2025-12-31 14:30:00 +0100

---

## Resumen Ejecutivo

- **Repositorios activos**: 3
- **Total de commits**: 87
- **Líneas añadidas**: 12345
- **Líneas eliminadas**: 6789

---

## `proyecto-alpha` — 40 commits (+1234/-567)

| Hash | Fecha | Mensaje |
|------|-------|---------|
| `a1b2c3d` | 2025-03-15 | Fix login timeout |
| `e4f5a6b` | 2025-03-16 | Add user validation |
```

## Exportación a PDF *(experimental)*

```bash
gitcrumb --pdf   # requiere Docker (usa la imagen marpteam/marp-cli)
```

Genera un archivo `.pdf` con el mismo nombre que el Markdown, en la misma ubicación. La conversión se ejecuta dentro de un contenedor Docker — no se instala nada en el host.

> **Nota:** la exportación a PDF está aún en fase de pruebas y puede no funcionar correctamente en todos los entornos.

## Flujo de ejecución

1. **Configuración** — Resuelve parámetros (CLI → interactivo → default).
2. **Validación** — Comprueba que la carpeta raíz exista y crea el directorio de salida si es necesario.
3. **Escaneo** — Busca recursivamente todos los directorios `.git` dentro de `--path`, respetando `.gitignore` del repositorio ancestro más cercano.
4. **Extracción** — Ejecuta `git log` por cada repositorio, filtrando por autor y rango de fechas. Una consulta separada por autor (evita regex OR) y dos pasadas (`--no-merges` + `--merges`) para distinguir commits propios de merges.
5. **Filtrado** — Solo incluye en el informe los repositorios con commits en el periodo.
6. **Generación** — Construye el Markdown desde `gitcrumb/report_template.md` con encabezado, resumen ejecutivo y tablas por repo (ordenados alfabéticamente).
7. **Escritura** — Guarda `.md` en `--output`. Si el contenido no ha cambiado respecto a una ejecución anterior (verificado por hash SHA-256), se salta la reescritura.
8. **Exportación PDF** *(opcional)* — Convierte a PDF vía Docker + Marp si se pasa `--pdf`.

Ver [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) para detalles del flujo interno y la arquitectura.
