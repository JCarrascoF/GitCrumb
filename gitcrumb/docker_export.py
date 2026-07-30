"""Ejecución de Docker — exportación PDF vía Marp CLI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from gitcrumb.i18n import t


MARP_IMAGE = "marpteam/marp-cli"


def check_docker() -> bool:
    """Check whether Docker is available and working."""
    try:
        return subprocess.run(
            ["docker", "info"], capture_output=True, text=True
        ).returncode == 0
    except FileNotFoundError:
        return False


def ensure_image(image: str) -> bool:
    """Pull the Docker image if it is not present locally."""
    inspect = subprocess.run(
        ["docker", "image", "inspect", image], capture_output=True, text=True,
    )
    if inspect.returncode == 0:
        return True

    print(t("docker.pulling", image=image))
    result = subprocess.run(
        ["docker", "pull", image], capture_output=True, text=True, timeout=300,
    )
    if result.returncode != 0:
        print(t("docker.pull_error", err=result.stderr.strip()), file=sys.stderr)
        return False
    return True


_MARP_FRONTMATTER = """---
marp: true
theme: default
size: A4
paginate: true
style: |
  section {
    width: 210mm;
    height: 297mm;
    padding: 20mm;
    justify-content: flex-start;
    font-size: 11pt;
  }
  h1 {
    border-bottom: 1px solid #ccc;
    padding-bottom: 8px;
  }
  h2 {
    margin-top: 24px;
  }
---
"""


def export_pdf(md_path: str) -> str | None:
    """Convert Markdown to PDF using Marp CLI inside a Docker container.

    Prepends the required YAML frontmatter so Marp renders an A4 document.
    Returns the path of the generated PDF or None on failure.
    """
    md_file = Path(md_path).resolve()
    pdf_path = md_file.with_suffix(".pdf")
    mount_dir = md_file.parent
    marp_name = str(md_file.name).replace(".md", ".marp.md")
    marp_path = mount_dir / marp_name

    # Prepend Marp frontmatter to the original Markdown
    md_text = md_file.read_text(encoding="utf-8")
    marp_path.write_text(_MARP_FRONTMATTER + md_text, encoding="utf-8")

    try:
        print(t("docker.generating"))
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{mount_dir}:/home/marp/app:z",
            MARP_IMAGE,
            marp_name,
            "--pdf",
            "-o", str(pdf_path.name),
        ]

        result = subprocess.run(
            cmd, stderr=subprocess.PIPE, timeout=120,
        )
        if result.returncode == 0 and pdf_path.exists():
            return str(pdf_path)

        stderr = result.stderr.decode(errors="replace").strip()
        print(t("docker.marp_error", err=stderr), file=sys.stderr)
        return None
    finally:
        marp_path.unlink(missing_ok=True)
