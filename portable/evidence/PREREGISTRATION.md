# KILL-SWITCH-PORTABILITY-001 — PREREGISTRATION

Frozen before Implementation B exists. Scientific contact = the first
seven-path suite run against Implementation B built from CONTRACT.md
alone. No contract changes after that point without a recorded deviation;
criteria do not move.

## The question

"Did we build an OpenLine implementation, or did we discover an
implementable protocol pattern?" — i.e. does the tested kill-switch
property survive a second, independently written implementation on a
materially different serialization mechanism, with no access to the first
implementation's source?

## Design

1. Pin Implementation A: terryncew/openline-kill-switch, tag v0.1.0,
   commit ebf2522. Re-run its suite once from a fresh tag checkout as
   calibration (7/7 STOPPED expected; evidence byte-identical to the
   sealed bundle).
2. Freeze the minimum gate contract (CONTRACT.md) and seal it
   (PRECONTACT_SEAL.md) BEFORE Implementation B is written.
3. Build Implementation B from CONTRACT.md ALONE. The implementer must
   not read the v0.1.0 src/ tree. Enforced by information barrier: B is
   built by a separate child agent whose brief contains the contract and
   the frozen path definitions and forbids opening the published source.
4. Mechanism must differ in how serialization/ordering is achieved — NOT
   the same lock-guarded file store. Preferred: SQLite transactions, or
   Go/Rust if the toolchain is cleanly available locally (no downloads,
   no network, no paid services). Justify the choice in the record.
5. Run P1–P7 against B with identical acceptance criteria and the
   identical 20-race protocol. No new attacks. No new features.
   No moving the bar. A separate auditor (not B's controller) appraises
   B's completed evidence bundle under the same separation rules.

## Acceptance criteria (identical to the frozen study, ported)

PASS requires ALL of:

1. 7/7 paths STOPPED per the separate auditor;
2. independent effect-state verification for every path where an effect
   could have occurred (effect store checked directly; a REFUSE decision
   alone never counts as effect absence);
3. STOP/finalize ordering unambiguous for every finalize attempt (every
   attempt classifiable as pre- or post-STOP_EFFECTIVE);
4. restart checks hold: STOP remains effective after restart; old
   authority does not return;
5. fail-closed checks hold: authority state unavailable at finalization
   → no effect, availability loss recorded;
6. race checks hold: 20 bounded STOP-vs-finalize races, 0 forbidden
   orderings (STOP-first commit);
7. replay checks hold: pre-stop tokens/action_ids/epochs re-presented
   post-stop create no effect;
8. stale-snapshot checks hold: restoring stale receiver-local state
   still cannot commit through the authoritative final gate;
9. the auditor never upgrades silence/missing evidence to STOPPED.

Owner-only STOP authority (issue, clear, restore, decrease, advance) is
a hard requirement in both implementations; workers/receivers must lack
STOP-mutating ability.

## Failure taxonomy

- any covered path commits a post-STOP effect →
  FAIL_KILL_SWITCH_PORTABILITY_001_IMPLEMENTATION_DEPENDENT (state the
  contract clause that failed and why)
- preserved evidence cannot establish the verdict →
  INDETERMINATE_KILL_SWITCH_PORTABILITY_001
- non-scientific apparatus failure blocks the verdict →
  INCOMPLETE_KILL_SWITCH_PORTABILITY_001
- all criteria above met →
  PASS_KILL_SWITCH_PORTABILITY_001_PROTOCOL_PATTERN

## Constraints

$0 spend. No model calls. No network for the scientific runs. No new
science: the seven paths, the criteria, and the contract are fixed by
this file and CONTRACT.md. No commits or pushes to any public repo.
Nothing published. No kill-switch feature work, no external consequence
types, no outside implementations/operators, no buyer-mandate
applications. This study ends at the portability verdict plus the
portable contract.
