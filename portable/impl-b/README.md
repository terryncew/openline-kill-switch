# Implementation B — kill-switch reference on SQLite transactions

The second, independently written implementation of the portable gate
contract (`../GATE_CONTRACT.md`; frozen contract in
`../evidence/CONTRACT.md`).

Provenance: built during KILL-SWITCH-PORTABILITY-001 (2026-09-19) from
the frozen contract alone. Information barrier: the builder never opened
Implementation A's source (`openline-kill-switch/src/`). Full study
record: `../evidence/RESULTS.md`.

## Mechanism

One SQLite database file is the shared serialization point:

- `stop_state` — single row, monotonic STOP epoch (`0` = ACTIVE,
  `>=1` = STOPPED) plus the journal rowid of the STOP transition.
  Durable, so STOP survives process/DB restart.
- `journal` — `INTEGER PRIMARY KEY AUTOINCREMENT`; every STOP
  transition, grant, preliminary admission, effect commit, and refusal
  appends a row. The rowid is the linearization order, never wall-clock.
  STOP_EFFECTIVE is the journal rowid of the owner STOP transition.
- `grants` — owner-issued authority tokens with their issuing journal
  rowid. A grant is live after STOP only if issued *after*
  STOP_EFFECTIVE.
- `effects` — the independent effect store. Rows are written only inside
  an admitting final-gate transaction.

The final gate (`GateDB.finalize`) is a single transaction: `BEGIN
IMMEDIATE`, read current authoritative STOP standing, decide
ADMIT/REFUSE, insert the ordered decision row, and — only on ADMIT —
the effect row, then `COMMIT`. If the database cannot be opened or the
transaction cannot run, no effect row can exist: fail closed, and the
harness records the availability loss.

Roles: `Owner` holds the study-local owner secret and is the only role
whose methods mutate STOP. `Worker` and `Receiver` are built without it
and expose no STOP-mutating method. Preliminary admission returns a
ticket explicitly marked non-authoritative. `Receiver.local_epoch` is a
deliberately stale-able cache (the P6 test); the gate never consults it.

## How this differs from Implementation A

- **Serialization:** the database engine's write serialization (`BEGIN
  IMMEDIATE`, single writer, commit order defines linearization) instead
  of an OS file lock guarding read-modify-write of files.
- **Atomicity scope:** STOP state, decision journal, grants, and effects
  live in one ACID store, so "read STOP standing + commit-or-refuse" is
  one transaction. No lock discipline to slip.
- **Ordering evidence:** journal AUTOINCREMENT rowids give the total
  commit order directly.

Same language family (Python 3.12 stdlib, `sqlite3` only), different
serialization mechanism and architecture — which is what the portability
study set out to vary.

## Reproduce

```sh
cd portable/impl-b
python3 run.py                                   # seven paths, controls B–F, 20 races
python3 auditor.py evidence/evidence.jsonl evidence/race_evidence.jsonl
```

No network. Stdlib only. `run.py` regenerates `evidence/` locally; the
deterministic bundle must match the frozen PASS copy byte-for-byte:

```sh
sha256sum evidence/evidence.jsonl
# bace02a6f08f4f15b780096ead4b5e76e3281873492e57924dbfe75ac5622be4
# (frozen copy: ../evidence/impl-b-evidence.jsonl)
```

(The race bundle is intentionally nondeterministic — real thread races;
only the invariant "0 forbidden orderings" is asserted.)

## Layout

- `killswitch_b/` — the implementation (`store.py`, `roles.py`,
  `evidence.py`)
- `run.py` — the run harness: P1–P7, controls B–F, 20-race protocol
- `auditor.py` — separate program; reads only the completed evidence
  bundle, verifies the hash chain, appraises each path STOPPED / ESCAPED
  / UNKNOWN
