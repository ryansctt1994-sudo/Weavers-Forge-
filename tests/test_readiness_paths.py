"""Adversarial checkout-scope tests for Forge's documentation readiness gate.

These tests do not fetch the network, follow links outside a test directory,
or qualify community receipts as technical verification.
"""
from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import check_repo


class ReadinessPathBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "checkout"
        self.root.mkdir()
        self.root_patch = patch.object(check_repo, "ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def _markdown(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def _reject(self, fn, fragment):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream), self.assertRaises(SystemExit) as e:
            fn()
        self.assertEqual(e.exception.code, 1)
        self.assertIn(fragment, stream.getvalue())

    def test_inside_checkout_regular_files_and_root_links_pass(self):
        self._markdown("docs/guide.md", "# Guide\n")
        self._markdown("README.md", "# Home\n[guide](/docs/guide.md#heading)\n")
        check_repo.check_markdown_files()
        check_repo.check_internal_links()

    def test_escaping_relative_link_is_rejected(self):
        self._markdown("README.md", "[secret](../secret.txt)\n")
        (self.root.parent / "secret.txt").write_text("external")
        self._reject(check_repo.check_internal_links, "escaping internal link")

    def test_symlinked_internal_link_is_rejected(self):
        external = self.root.parent / "outside.md"
        external.write_text("externally supplied text\n")
        (self.root / "outside.md").symlink_to(external)
        self._markdown("README.md", "[read](outside.md)\n")
        self._reject(check_repo.check_internal_links, "escaping internal link")

    def test_symlinked_markdown_document_is_rejected(self):
        external = self.root.parent / "outside.md"
        external.write_text("# File\n")
        (self.root / "foreign.md").symlink_to(external)
        self._reject(check_repo.check_markdown_files, "escapes the repository")

    def test_required_markdown_symlink_is_not_counted_as_checked_in(self):
        for name in check_repo.REQUIRED_FILES:
            self._markdown(name, "Valid\n")
        outside = self.root.parent / "replacement.md"
        outside.write_text("replacement\n")
        (self.root / check_repo.REQUIRED_FILES[0]).unlink()
        (self.root / check_repo.REQUIRED_FILES[0]).symlink_to(outside)
        self._reject(check_repo.check_required_files, "escapes the repository")

    def test_missing_internal_link_is_rejected(self):
        self._markdown("README.md", "[missing](docs/absent.md)\n")
        self._reject(check_repo.check_internal_links, "broken internal link")


if __name__ == "__main__":
    unittest.main()
