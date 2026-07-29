"""Tests TDD: round-trip de hash en report.py.

Bug original: `read_existing_hash` usaba `_GITRACK_HASH_SUFFIX[1:]` que es `'-->\n'`,
pero `splitlines()` quita los saltos de línea al iterar → `.endswith('-->\n')` nunca
matchea y el hash leído devuelve None. Esto hacía que `write_report` reescribiera
el archivo en cada ejecución aunque el contenido no hubiera cambiado.

Rastro:
  _GITRACK_HASH_SUFFIX = ' -->\n'
  _GITRACK_HASH_SUFFIX[1:]    → '-->\n'   (incluye \n)
  splitlines()                 → quita \n
  stripped.endswith('-->\n')   → False siempre
"""

import unittest
from pathlib import Path
from tempfile import NamedTemporaryFile


class TestHashRoundTrip(unittest.TestCase):

    def test_read_returns_same_hash_that_was_written(self):
        """Caso mínimo: escribir un hash y leerlo de vuelta.

        El archivo contiene una línea como:
            <!-- gitrack-hash: abc123def456 -->
        (sin \n al final porque splitlines() lo quita).

        read_existing_hash debe devolver 'abc123def456'."""
        with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            # Simula exactamente lo que write_report produce (splitlines lo lee sin \n):
            f.write("# Content\n")
            f.write("<!-- gitrack-hash: abc123def456 -->\n")
            path = Path(f.name)

        try:
            from gitrack.report import read_existing_hash
            result = read_existing_hash(path)
            self.assertIsNotNone(result, "read_existing_hash returned None — el hash no se leyó")
            self.assertEqual(result, "abc123def456")
        finally:
            path.unlink()

    def test_write_skips_when_content_unchanged(self):
        """Si el hash coincide, write_report debe devolver False (no reescribe)."""
        with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            # Escribe manualmente lo que write_report produciría:
            f.write("# Original\n")
            f.write("<!-- gitrack-hash: samehash -->\n")
            path = Path(f.name)

        try:
            from gitrack.report import write_report
            written = write_report(path, "# New body", "samehash")
            self.assertFalse(written, "write_report reescribió aunque el hash coincidía")
        finally:
            path.unlink()


if __name__ == "__main__":
    unittest.main()
