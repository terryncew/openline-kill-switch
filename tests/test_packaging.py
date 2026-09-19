"""Packaging hermeticity tests for the openline-kill-switch publication candidate.

Stdlib only. These tests verify the standalone-clone properties; they do
not test the kill-switch mechanism itself (that is the probe suite in
src/, run via ./RUN.sh).

Run:  python3 -m unittest discover -s tests -v   (from the repo root)
"""
from __future__ import annotations

import ast
import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"


def py_files():
    return sorted((SRC).glob("*.py"))


def imports_of(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mods.add(node.module.split(".")[0])
    return mods


class TestHermetic(unittest.TestCase):
    def test_no_absolute_host_paths(self):
        bad = []
        for p in py_files():
            text = p.read_text(encoding="utf-8")
            for pat in ("/home/", "/workspace/", "expanduser", "~/."):
                if pat in text:
                    bad.append((p.name, pat))
        self.assertEqual(bad, [], f"host-specific paths found: {bad}")

    def test_no_network_imports(self):
        stdlib_net = {"socket", "urllib", "http", "requests", "ssl",
                      "ftplib", "smtplib", "xmlrpc"}
        bad = []
        for p in py_files():
            hit = imports_of(p) & stdlib_net
            if hit:
                bad.append((p.name, sorted(hit)))
        self.assertEqual(bad, [], f"network imports found: {bad}")

    def test_receiver_closure_key_free(self):
        # The D3 property: no module reachable from receiver.py may import
        # stop_authority or define OWNER_KEY.
        graph = {p.stem: imports_of(p) for p in py_files()}
        local = {p.stem for p in py_files()}
        seen, stack = set(), ["receiver"]
        while stack:
            mod = stack.pop()
            if mod in seen or mod not in local:
                continue
            seen.add(mod)
            stack.extend(graph[mod] & local)
        self.assertNotIn("stop_authority", seen,
                         f"receiver closure imports stop_authority: {seen}")
        for mod in seen:
            text = (SRC / f"{mod}.py").read_text(encoding="utf-8")
            self.assertNotIn("OWNER_KEY", text,
                             f"OWNER_KEY material in receiver-reachable {mod}.py")

    def test_owner_key_defined_once(self):
        hits = []
        for p in py_files():
            if re.search(r"^OWNER_KEY\s*=", p.read_text(encoding="utf-8"),
                         re.M):
                hits.append(p.name)
        self.assertEqual(hits, ["stop_authority.py"],
                         f"OWNER_KEY defined in: {hits}")

    def test_vendored_store_pinned(self):
        vendored = SRC / "vendor" / "_durable_heads.py"
        self.assertTrue(vendored.is_file(), "vendored store missing")
        digest = hashlib.sha256(vendored.read_bytes()).hexdigest()
        doc = (SRC / "vendor" / "VENDORING.md").read_text(encoding="utf-8")
        self.assertIn(digest, doc,
                      "vendored sha256 not pinned in VENDORING.md")


if __name__ == "__main__":
    unittest.main()
