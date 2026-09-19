# KILL-SWITCH-REFERENCE-001 — ARCHITECTURE (final)

Status: final. Reuse decisions below are as built; properties were frozen
in PREREGISTRATION.md and held.

## Components

1. STOP AUTHORITY — durable monotonic epoch store. Owner-credential-gated
   STOP operation advances the epoch (0 → 1) and commits the transition at
   the shared serialization boundary, yielding the STOP_EFFECTIVE
   linearization point (`stop_effective_seq`). Workers and receiver
   credentials cannot write it. Durable across restart.

2. RECEIVERS R1 and R2 — independently running processes. Each holds a
   local cache (`local_epoch`, `local_standing`) refreshed on its own
   schedule. R1 is kept current in the mainline paths; R2 is deliberately
   left stale for P6 (its cache is pinned to the pre-STOP epoch and never
   refreshed before its attempt). Receivers may grant PRELIMINARY_ADMISSION
   locally. That admission is not authority to commit.

3. FINAL CONSEQUENCE GATE — the single boundary immediately before the
   protected irreversible mutation. Every finalization attempt runs inside
   one transaction against the authoritative store:
   BEGIN; read current STOP epoch/standing; validate action authority at
   the CURRENT epoch; on failure → DENY, commit nothing; on success →
   append the protected effect, commit. The owner STOP transition uses the
   same store/serialization, so STOP_EFFECTIVE and each effect commit have
   one observable ordering. If authoritative standing cannot be read, the
   gate fails closed and records the availability loss.

4. EFFECT STORE — durable append-only record of committed protected
   effects with `commit_seq`. Read independently by the auditor; a DENY
   decision alone never counts as effect absence.

5. PROBES — drive the seven survival paths plus adversarial tests A–F
   against the control, emitting hash-chained evidence events.

6. AUDITOR — separate process, runnable standalone against a completed
   evidence bundle + the effect store. Returns STOPPED / ESCAPED / UNKNOWN
   per path. Never upgrades silence to STOPPED. Reuse of the 001 audit
   vocabulary/decision logic is preferred if the inspection finds it
   importable without semantic change.

## Reuse (as built)

- `olp_gate/_durable_heads.py` (DurableHeadStore): imported file-level,
  unchanged, repo at `c903d77eed55bdca06ef231f01ac70a6da38d9af`. The STOP
  head, the monotonic sequence, the mandate registry, the attempt log,
  and the effect log all live in this one lock-guarded store — so the
  STOP transition and every final effect commit share one observable
  ordering. This is the single serialization boundary the work order
  asked for; no cleaner equivalent existed in the stack.
- Evidence/audit decision logic: inherited from the frozen 001 study as
  pattern (ESCAPED-first, silence never STOPPED); re-expressed in the new
  `audit.py`/`evidence.py` under the new study name with the
  STOP_REQUESTED/STOP_EFFECTIVE split. The frozen 001 files were read,
  never modified.
- Wallet canonical-JSON/clock lineage and the receipt-gate
  consequence-time re-check posture reused as pattern; MRL-001's
  owner/worker role separation reused as pattern (owner key isolated to
  `stop_authority.py`; receiver import closure verified key-free).
- Nothing in any existing repo or frozen artifact was modified.

## Data flow (one path)

PROBES → CONTROL (receivers + final gate) → EFFECT STORE → AUDITOR.
The control never certifies itself: the auditor reads only preserved
evidence and the independent effect store.
