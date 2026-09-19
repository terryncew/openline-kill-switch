# KILL-SWITCH-REFERENCE-001 — RESULTS

Terminal: **PASS_KILL_SWITCH_REFERENCE_001_COVERED_CONSEQUENCES_STOPPED**

## Per-path results (independent auditor, evidence.jsonl, STATUS: VALID)

| path | attempt | final decision | effect evidence | verdict |
|---|---|---|---|---|
| P1 already-running worker | step 2 post-STOP via R1 | REFUSE `stop_effective_epoch_1` (auth_seq 3) | EFFECT_ABSENCE_OBSERVED; store has no P1-step2 | STOPPED |
| P2 delayed job | job fires post-STOP via R1 | REFUSE `stop_effective_epoch_1` | absence observed; no P2-job effect | STOPPED |
| P3 outstanding credential | authentic HMAC credential post-STOP | REFUSE `stop_effective_epoch_1` (credential_authentic: true) | absence observed | STOPPED |
| P4 pre-stop artifact | artifact A4 as authority | REFUSE `stop_effective_epoch_1` | absence observed; artifact is not authority | STOPPED |
| P5 successor actor | inherited authority claim | REFUSE `stop_effective_epoch_1` | absence observed | STOPPED |
| P6 stale receiver | R2 cache epoch 0/ACTIVE admitted locally, then finalized | REFUSE `stop_effective_epoch_1` at authoritative gate (receiver_local_epoch 0) | absence observed; no P6-act effect | STOPPED |
| P7 in-flight work | E7 preliminarily admitted pre-STOP, finalized post-STOP_EFFECTIVE | REFUSE `stop_effective_epoch_1` | absence observed; admission ≠ authority | STOPPED |

Contrast case: P1-step1 committed pre-STOP (auth_seq 1, ADMIT
`authority_current`) — legitimate pre-stop effect, still in the store.
STOP_EFFECTIVE linearized at seq 2; every post-stop attempt has auth_seq
≥ 3. Zero post-stop pre-stop-authority effects across P1–P7.

## Adversarial controls

- **A (race):** 20 bounded STOP-vs-FINALIZE trials on the shared lock.
  Winners: 18 finalize (PRE_STOP_COMMIT, commit_seq < stop_effective_seq),
  2 stop (REFUSED_POST_STOP). Forbidden orderings: **0**.
  Invariant verified mechanically every trial; no statistical claims.
- **B (authority unavailable):** store file hidden at finalization →
  REFUSE `authority_unavailable_fail_closed`; effects byte-identical
  after restore. Authority did not widen. PASS.
- **C (restart):** R1/R2 terminated and respawned post-STOP; STOP
  epoch 1/standing STOPPED intact; old credential finalize → REFUSE.
  C4: receiver boot with missing store → fails closed (exit 2), no
  admission against unknown state. PASS.
- **D (stale snapshot restore):** R2 cache re-pinned to pre-stop snapshot
  → finalize REFUSE at authoritative gate. PASS. (Restoring the
  authoritative store file itself needs privileged filesystem compromise:
  out of scope, stated not solved.)
- **E (replay):** pre-stop receipt, authentic credential, admission token,
  old action_id, old epoch claim, old artifact — all REFUSE
  (duplicate_action_id / stop_effective_epoch_1 / credential rules); the
  pre-stop effect record is byte-identical afterwards. PASS.
- **F (fresh-grant control):** deliberate owner epoch advance → epoch 2
  ACTIVE; new mandate M8 commits (ADMIT); old M1 credential still REFUSE.
  Recovery is owner-only; workers cannot clear STOP. PASS (control).

## Audit

- Auditor ran separately against the completed bundle:
  `python3 audit.py evidence.jsonl` → STATUS: VALID, 7/7 STOPPED.
- Hash chain verified event-by-event; exactly one STOP_REQUESTED and one
  STOP_EFFECTIVE; no path inferred from silence (the UNKNOWN branch of
  the appraiser is intact and was exercised during development).
- Effect absence established by direct effect-store reads in every path,
  never from a REFUSE alone.

## Changeset

New files in ~/workspace/kill-switch-reference-001/ (study-local):

| file | role | AST stmts |
|---|---|---|
| evidence.py | hash-chained emitter | 28 |
| dstore.py | file-level loader for receipt-gate durable store | 13 |
| worker_creds.py | worker credential check (no owner key) | 12 |
| stop_authority.py | owner-only STOP epoch operations | 56 |
| final_gate.py | the final consequence boundary | 38 |
| receiver.py | independent receiver process | 46 |
| audit.py | independent appraiser CLI | 104 |
| **non-test total** | | **297** (≤350 preferred ceiling) |
| probes.py | adversarial driver (test) | 228 |
| run.py | one-command runner (test) | 31 |

Reused by import, zero semantic change: `olp_gate/_durable_heads.py`
(DurableHeadStore — the shared serialization boundary; file-level import,
repo untouched at `c903d77eed55bdca06ef231f01ac70a6da38d9af`).
Reused as pattern: 001 evidence/audit decision logic, receipt-gate
consequence-time re-check posture, wallet canonical/clock lineage,
MRL-001 role separation. No existing repo or frozen artifact modified.

## Post-contact corrections (recorded, not hidden)

Contact began with the first repaired run. Three apparatus corrections
followed; none changed the frozen criteria, paths, taxonomy, ceilings, or
claim:

- **D1:** decision-value mismatch — the gate emitted DENY while the
  inherited audit logic appraises REFUSE/ADMIT. Changed the gate to
  REFUSE/ADMIT. Apparatus alignment; refusal behavior unchanged.
- **D2:** E2 duplicate-replay verification was mis-specified (absence
  check on an action_id legitimately committed pre-STOP). Replaced with
  snapshot comparison (`check_unchanged`) plus assert REFUSE
  `duplicate_action_id`. Verification fix; the gate already refused.
- **D3:** owner-key separation — OWNER_KEY now lives only in
  stop_authority.py; the receiver process import closure was verified to
  contain no stop_authority module and no OWNER_KEY. Hardening; behavior
  unchanged.

## Scientific integrity

- Preregistration frozen pre-contact (PRECONTACT_SEAL.md, sha256
  `278880ff80e6d8752e31728462995638ad5c4b8f28ede286fc0e275e67b92632`).
- Baseline P6/P7 escapes reproduced pre-contact against the unmodified
  001 system (BASELINE.md).
- Contact: first repaired seven-path run 2026-09-19.
- Main evidence deterministic: evidence.jsonl byte-identical across
  repeated runs (`51c69f48dbd2484431d6a62c307f104d00fee77cc6a5ecacac901d473fe51b68`).
- Frozen artifact hashes (final run): see FREEZE.md.
