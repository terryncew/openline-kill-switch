# Vendoring provenance

`_durable_heads.py` is a byte-identical copy of
`olp_gate/_durable_heads.py` from `terryncew/openline-receipt-gate`
at commit `c903d77eed55bdca06ef231f01ac70a6da38d9af` (remote main,
verified read-only during KILL-SWITCH-REFERENCE-001).

- sha256: `33d2738849b325f69ef909b1153ec33d571415e0c32941b8cda79e1ba95c5509`
- License: MIT, Copyright (c) 2026 Terrynce White (same author; see
  `../../LICENSE`). Vendoring permitted.
- Reason for file-level copy instead of dependency: the module is loaded
  by path (`dstore.py`) without importing the `olp_gate` package, which
  would pull an Ed25519 dependency this reference does not need. This
  follows the KSQ-001 precedent: reuse the tested mechanism, change
  nothing in the existing repo.
- The module is stdlib-only (`fcntl`, `json`, `os`, `tempfile`,
  `threading`, `typing`). It provides the lock-guarded durable store that
  is the single serialization boundary for STOP transitions and final
  effect commits.

Do not modify this file. If the upstream changes, re-vendor deliberately
and re-run the full suite; the frozen evidence in `evidence/frozen/`
pins the behavior this release was sealed against.
