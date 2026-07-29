"""Tests para models.py — dataclasses Commit y RepoResult."""

import unittest
from gitrack.models import Commit, RepoResult


class TestCommit(unittest.TestCase):
    def test_creation(self):
        c = Commit(short_hash="a1b2c3d", date="2025-03-15", message="Fix login")
        self.assertEqual(c.short_hash, "a1b2c3d")
        self.assertEqual(c.date, "2025-03-15")
        self.assertEqual(c.message, "Fix login")


class TestRepoResult(unittest.TestCase):
    def test_total_property(self):
        r = RepoResult(name="repo", commits=[Commit("a", "d", "m"), Commit("b", "d", "m")])
        self.assertEqual(r.total, 2)

    def test_total_empty(self):
        r = RepoResult(name="empty")
        self.assertEqual(r.total, 0)

    def test_default_fields(self):
        r = RepoResult(name="repo")
        self.assertEqual(r.added, 0)
        self.assertEqual(r.deleted, 0)
        self.assertEqual(r.merges, 0)
        self.assertEqual(r.merge_hashes, set())


if __name__ == "__main__":
    unittest.main()
