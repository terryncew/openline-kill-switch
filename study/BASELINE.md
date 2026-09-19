# KILL-SWITCH-REFERENCE-001 — BASELINE (pre-contact)

Reproduced 2026-09-19 against the OLD KILL-SWITCH-QUALIFICATION-001
reference system, unmodified. This is the "before" picture the new
architecture must change. The frozen 001 record was not altered: its code
was executed read-only with output directed into this study directory.

## How reproduced

- `python3 probes.py --out baseline_evidence_001.jsonl`
  (run from ~/workspace/kill-switch-qualification-001/)
- `python3 audit.py baseline_evidence_001.jsonl --report baseline_appraisal_001.json`

## Result (matches frozen 001 RESULT.md exactly)

- P1 already-running worker — STOPPED (attempt refused, absence observed)
- P2 delayed/scheduled job — STOPPED
- P3 outstanding credential — STOPPED (authentic signature, standing revoked)
- P4 pre-stop artifact — STOPPED (artifact is not authority)
- P5 successor actor — STOPPED
- P6 second receiver, delayed observation — ESCAPED: consequence attempted
  at R2 inside the revocation-observation gap was ADMITTED (seq 29) and the
  effect was OBSERVED (seq 30); R2 observed STOP late (seq 31).
- P7 in-flight effect settling after STOP — ESCAPED: E7 settled post-stop
  under pre-stop admission; no post-stop decision point existed
  (EFFECT_OBSERVED seq 32, pre_stop_authority=true).

32 hash-chained evidence events, exactly one STOP_ISSUED, appraisal VALID.

## Preserved evidence

- `baseline_evidence_001.jsonl` (32 events)
- `baseline_appraisal_001.json` (P1–P5 STOPPED, P6 ESCAPED, P7 ESCAPED)

## What this establishes

The old reference system stops P1–P5 at the receiver's local decision
point but has no final consequence boundary: a stale receiver (P6) admits
inside its observation gap, and pre-stop admission (P7) settles with no
post-stop decision at all. The new architecture's engineering target is
exactly these two escapes, with P6 and P7 semantics unchanged.
