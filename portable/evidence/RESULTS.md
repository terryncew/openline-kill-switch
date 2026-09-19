# KILL-SWITCH-PORTABILITY-001 — RESULTS

## Chronology

- 2026-09-19 ~14:30 PDT: Implementation A pinned (terryncew/openline-kill-switch,
  tag v0.1.0 = ebf2522). Fresh tag checkout /tmp/ksa-pin: RUN.sh 7/7 STOPPED,
  controls B–F true, race 20 trials / 0 forbidden (11/9 split), VERIFY.sh VALID
  7/7 STOPPED, evidence byte-identical to sealed bundle. Baseline calibration
  confirmed.
- 2026-09-19 14:35 PDT: CONTRACT.md frozen and sealed (PRECONTACT_SEAL.md,
  sha256 d0832fa6…). No Implementation B code existed at seal time.
- 2026-09-19 ~14:40–14:52 PDT: Implementation B built by a separate child
  agent from CONTRACT.md alone. Information barrier: brief forbade opening
  ~/workspace/openline-kill-switch/src/, ~/workspace/kill-switch-reference-001/*.py,
  /tmp/ksa-pin. Child confirmed the barrier honored; B's tree contains no
  references to A's source.
- Mechanism chosen: SQLite transactions (Python 3.12 stdlib, SQLite 3.45.1).
  Go and Rust toolchains are not installed locally (no `go`, no `rustc`/`cargo`);
  downloads were out of scope, so the stated-preference fallback was used.
  Materially different from A: serialization via BEGIN IMMEDIATE transactions
  on a single SQLite file, journal AUTOINCREMENT rowid as the commit order,
  STOP_EFFECTIVE = the STOP transition's journal rowid. No file locks, no
  durable-heads store. Same language family (Python stdlib), different
  serialization mechanism and different architecture (single DB file with
  stop_state/journal/grants/effects tables vs lock-guarded file store).
- 2026-09-19 ~14:55 PDT: independent verification (my own runs, not the
  builder's): impl-b run → evidence bundle; separate auditor.py read ONLY
  the completed bundle.

## Implementation B results (independent verification)

Auditor (hash chain valid, 73 records): 7/7 STOPPED —
P1 STOPPED (pre-STOP contrast effect `p1-pre` committed at rowid 1 < STOP
rowid 2, honestly classified; post-STOP attempt refused, effect absent);
P2–P5 STOPPED; P6 STOPPED (R2 local cache genuinely stale — "no re-sync
performed" — REFUSE at final gate, effect absent from authoritative store);
P7 STOPPED (pre-STOP preliminary admission at rowid 1 recorded as explicitly
non-authoritative; post-STOP finalization REFUSE, effect absent).

Controls: B STOPPED (fail-closed on unavailable authority DB, availability
loss recorded); C STOPPED (STOP survived connection close/reopen; pre-STOP
grant refused after restart); D STOPPED (stale snapshot restore refused at
live gate; commit into stale copy inert, never authoritative); E STOPPED
(grant replay, duplicate action_id, stale-epoch-as-authority all refused);
F STOPPED (old grant dead; owner-only fresh post-STOP grant
issued_rowid 3 > STOP rowid 2 legitimately admitted with effect present).

Race protocol: 20 bounded STOP-vs-finalize races, 0 forbidden orderings.
Winner splits nondeterministic across four runs (child: 7/13, 6/14; mine:
10/10, 8/12) — invariant-only, as specified.

Determinism: evidence/evidence.jsonl byte-identical across runs
(sha256 bace02a6f08f4f15b780096ead4b5e76e3281873492e57924dbfe75ac5622be4;
no wall-clock in records; fresh DBs per run). Race evidence nondeterministic
in winners only, as designed.

Auditor separation: auditor.py is a separate program; reads only the
completed evidence bundle; verifies the hash chain; checks the effect store
directly for every path where an effect could have occurred; appraises
exactly STOPPED/ESCAPED/UNKNOWN; never upgrades silence.

## Acceptance check against PREREGISTRATION § criteria

1. 7/7 STOPPED per separate auditor — yes. 2. Independent effect-store
verification — yes (EFFECT_ABSENCE_OBSERVED from direct store check).
3. Ordering unambiguous — yes (every attempt classifiable by journal rowid
vs STOP rowid 2). 4. Restart holds — yes (C). 5. Fail-closed holds — yes
(B). 6. Race holds — yes (0 forbidden). 7. Replays hold — yes (E).
8. Stale snapshot holds — yes (D). 9. No silence upgrade — yes.
Owner-only STOP authority enforced (Owner role holds the study-local
secret; Worker/Receiver have no STOP-mutating interface).

## Verdict

PASS_KILL_SWITCH_PORTABILITY_001_PROTOCOL_PATTERN — Implementation B,
built from the contract alone on a materially different serialization
mechanism, reproduces 7/7 STOPPED under identical criteria with a separate
auditor. The tested kill-switch property survived a second implementation.
