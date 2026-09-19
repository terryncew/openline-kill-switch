# PUBLICATION FIXES

Corrections made while packaging the frozen scientific result as a
standalone repository. Packaging/reproducibility defects only.

## #1 — vendored durable-store module (2026-09-19)

- File: `src/dstore.py`
- Problem: the study tree loaded `olp_gate/_durable_heads.py` from an
  absolute path inside another local checkout
  (`/home/hatch/workspace/openline-receipt-gate/...`). A fresh clone
  would fail without that checkout.
- Fix: vendored the file byte-identical into `src/vendor/_durable_heads.py`
  (sha256 `33d2738849b325f69ef909b1153ec33d571415e0c32941b8cda79e1ba95c5509`,
  provenance in `src/vendor/VENDORING.md`, MIT same-author license) and
  pointed the loader at the path relative to `dstore.py`.
- Mechanism impact: none. Same bytes, same lock-guarded store, same
  serialization boundary. The live run reproduces the frozen evidence
  bundle byte-identically (see `evidence/README.md`).

No other source changes. No change to: kill-switch mechanism, STOP
semantics, final consequence semantics, evidence meaning, P1–P7 semantics,
acceptance criterion, or scientific result.
