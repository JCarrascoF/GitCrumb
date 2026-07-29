"""Tests de round-trip para report.py — hash escrito y leído correctamente.

Bug original: `read_existing_hash` usaba `_GITRACK_HASH_SUFFIX[1:]` que incluye `\n`,
pero `splitlines()` quita los saltos de línea → la comparación `.endswith()` fallaba
y el hash nunca se leía. Esto hacía que `write_report` reescribiera el archivo
en cada ejecución aunque el contenido no hubiera cambiado.
"""

import unittest
from pathlib import Path
from tempfile import NamedTemporaryFile

from gitrack.models import Commit, RepoResult
from gitrack.report import read_existing_hash, write_report, generate_report_md


class TestHashRoundTrip(unittest.TestCase):
    """El hash que escribe `write_report` debe ser leíble por `read_existing_hash`."""

    def test_read_returns_same_hash_that_was_written(self):
        """Caso mínimo: escribir un hash y leerlo de vuelta."""
        with NamedTemporaryFile(suffix=".md", delete=False) as f:
            path = Path(f.name)

        try:
            written = write_report(path, "# Content", "abc123def456")
            self.assertTrue(written)

            read_back = read_existing_hash(path)
            self.assertEqual(read_back, "abc123def456")
        finally:
            path.unlink(missing_ok=True)

    def test_write_skips_when_content_unchanged(self):
        """Si el hash coincide, `write_report` no debe reescribir."""
        with NamedTemporaryFile(suffix=".md", delete=False) as f:
            path = Path(f.name)

        try:
            # Primera escritura
            write_report(path, "# Original content", "hash001")

            # Segunda llamada con el mismo hash → debe saltar
            skipped = write_report(path, "# Different body but same hash", "hash001")
            self.assertFalse(skipped)

            # El archivo conserva el contenido original
            content = path.read_text(encoding="utf-8")
            self.assertIn("# Original content", content)
        finally:
            path.unlink(missing_ok=True)

    def test_full_roundtrip_generate_write_read(self):
        """Flujo completo: generar → escribir → leer hash → saltar reescritura."""
        results = [RepoResult(
            name="test-repo",
            commits=[Commit("h1", "2025-03-01", "Test commit")],
            added=10, deleted=5, merges=0, merge_hashes=set(),
        )]

        with NamedTemporaryFile(suffix=".md", delete=False) as f:
            path = Path(f.name)
        path.unlink()  # start fresh — write_report creates it

        try:
            content_body, hash_val = generate_report_md(
                results, "test@dev.com", "2025-01-01", "2025-12-31", "/tmp/root"
            )

            # Primera escritura
            written_1 = write_report(path, content_body, hash_val)
            self.assertTrue(written_1)

            # Leer el hash de vuelta
            read_back = read_existing_hash(path)
            self.assertEqual(read_back, hash_val)

            # Segunda llamada con mismo contenido → debe saltar
            written_2 = write_report(path, content_body, hash_val)
            self.assertFalse(written_2)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
