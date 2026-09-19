# METHODOLOGY

How the result was earned — the controls that keep this an experiment
rather than a demo.

## Preregistration

The architecture properties, STOP_REQUESTED vs STOP_EFFECTIVE semantics,
the final-effect linearization point, all seven survival paths, the exact
PASS criterion, the failure taxonomy, the evidence schema, crash/restart
and race cases, the complexity ceiling, and the claim ceiling were frozen
*before* the new architecture first ran. `study/PREREGISTRATION.md`;
seal hashes in `study/PRECONTACT_SEAL.md`.

## Baseline

Before building the control, the two previously-escaped paths (P6 stale
receiver, P7 in-flight work) were reproduced against the old reference
system and their evidence preserved (`study/BASELINE.md`). The point was
to show exactly what changed.

## Scientific contact

Contact = the first run of the repaired control against the frozen
seven-path suite. After contact: no semantic tuning. Three apparatus
corrections were recorded openly in `study/RESULTS.md` (D1 gate vocabulary
alignment, D2 replay-verification fix, D3 owner-key isolation); none
changed the frozen criteria, paths, taxonomy, ceilings, or claim.
`study/D3_INTEGRITY_AUDIT.md` reconstructs D3 chronologically and
classifies it as mechanical conformance plumbing.

## Evidence, not assertion

Every run emits a hash-chained evidence bundle (`evidence.jsonl`) with a
fixed vocabulary: STOP_REQUESTED, STOP_EFFECTIVE, PRELIMINARY_ADMISSION,
POST_STOP_ATTEMPT, DECISION, EFFECT_OBSERVED / EFFECT_ABSENCE_OBSERVED /
UNKNOWN, plus the monotonic sequence that decides ordering. The main
bundle is deterministic — byte-identical across runs
(sha256 `51c69f48dbd2484431d6a62c307f104d00fee77cc6a5ecacac901d473fe51b68`;
the frozen copy is in `evidence/frozen/`).

## Independent appraisal

The auditor (`src/audit.py`) runs separately against the completed bundle
(`./VERIFY.sh`). It re-derives STOPPED / ESCAPED / UNKNOWN per path from
the evidence alone. Silence is never upgraded. Effect absence comes only
from direct effect-store reads. A REFUSE decision alone proves nothing.

## Adversarial controls

Beyond the seven paths: bounded STOP-vs-finalize races (20 trials, 0
forbidden orderings — defect-finding, not proof), authority-unavailable
fail-closed, restart of every component, stale-snapshot restore, replay of
every pre-stop artifact, and owner-only epoch-advance recovery. All in
`study/RESULTS.md`.
