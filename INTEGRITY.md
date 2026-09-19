# INTEGRITY

What changed after scientific contact, what did not, and how to check.

## Post-contact corrections (all disclosed in study/RESULTS.md)

- **D1** — the gate emitted DENY while the inherited audit logic appraises
  REFUSE/ADMIT. The gate vocabulary was aligned. Refusal behavior unchanged.
- **D2** — the E2 replay check was mis-specified (it tested absence on an
  action_id legitimately committed pre-STOP). Replaced with snapshot
  comparison plus assert REFUSE `duplicate_action_id`. Verification fix;
  the gate already refused.
- **D3** — owner-key isolation: the owner key now lives only in
  `src/stop_authority.py`, and the receiver process import closure was
  verified to contain no owner-key material. Hardening; behavior unchanged.
  Full chronological reconstruction and classification in
  `study/D3_INTEGRITY_AUDIT.md`: **D3_MECHANICAL_CONFORMANCE** — the frozen
  owner-credential gate is byte-for-byte the same mechanism before and
  after; key-module placement was never a frozen property (the
  preregistration explicitly permitted file-layout changes); no path
  semantics, ordering, criterion, or claim changed.
  Limitation: the study directory had no version control, so the exact
  pre-D3 key placement is not recoverable — the classification rests on
  verifiable facts (unchanged preregistration, unchanged gate, unchanged
  behavior/evidence semantics), not on the unknown. This is not presented
  as a perfectly reconstructable first-contact implementation.

## Seal note

`study/PRECONTACT_SEAL.md` pins sha256 hashes of the frozen pre-contact
documents. All verify byte-identical except `study/ARCHITECTURE.md`, which
was updated post-contact to document the as-built reuse outcome (including
the D3 verification). The normative freeze — `study/PREREGISTRATION.md` —
is unchanged and verifies. The sealed hash is preserved in the seal file
for independent checking; the update is disclosed here rather than hidden.

## What the publication candidate changed vs the study tree

Exactly one source change, recorded in `PUBLICATION_FIXES.md`:

1. `src/dstore.py` loads the durable-store module from the vendored copy
   (`src/vendor/_durable_heads.py`) instead of an absolute path into
   another checkout. The vendored bytes are identical (sha256 pinned in
   `src/vendor/VENDORING.md`). No mechanism change.

Everything else is file layout (`src/`, `tests/`, `evidence/`, `study/`)
and documentation. The mechanism, STOP semantics, final-gate semantics,
evidence meaning, path semantics, acceptance criterion, and scientific
result are untouched. The live run reproduces the frozen evidence bundle
byte-identically (see `evidence/README.md`).

## Reproduce it yourself

```sh
git clone <this-repo> && cd openline-kill-switch
./RUN.sh      # produces evidence/frozen-equivalent bundle in src/
./VERIFY.sh   # independent audit
```

Compare `src/evidence.jsonl` against `evidence/frozen/evidence.jsonl`:
the main bundle is deterministic and must match byte-for-byte. (The race
bundle is intentionally nondeterministic — real thread races; only the
invariant "0 forbidden orderings" is asserted.)
