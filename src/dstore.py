"""File-level loader for the receipt-gate durable store (vendored reuse).

Uses the vendored copy at vendor/_durable_heads.py (see vendor/VENDORING.md),
loaded by path without importing the olp_gate package (which would pull the
Ed25519 dependency this study does not need). Follows the KSQ-001 ref/
precedent: reuse the tested mechanism, change nothing in the existing repo.

Packaging note (PUBLICATION_FIXES.md #1): the study tree loaded this file
from an absolute path inside another checkout; the publication candidate
vendors it so a fresh clone has no dependency on any other checkout.
The vendored bytes are identical (sha256 pinned in vendor/VENDORING.md);
no mechanism change.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_MOD = str(Path(__file__).resolve().parent / "vendor" / "_durable_heads.py")

_spec = importlib.util.spec_from_file_location("ksr001_durable_heads", _MOD)
_dh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_dh)

DurableHeadStore = _dh.DurableHeadStore
DurableHeadStoreError = _dh.DurableHeadStoreError

IDENTITY = {"study": "KILL-SWITCH-REFERENCE-001", "store": "stop-authority-v1"}


def open_store(path: str):
    """Open the existing authoritative store. Fails closed (raises
    DurableHeadStoreError) if the file is missing, corrupt, or untrusted."""
    return DurableHeadStore(path, IDENTITY)
