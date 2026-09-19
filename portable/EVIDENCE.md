# Evidence

The minimum a conforming implementation must emit so a separate checker
can re-derive every verdict without trusting the live system. Semantic
requirements, not a wire format — neither reference implementation's
exact record layout is mandatory.

## Required record types

Keep these eight kinds of fact distinct:

- **STOP issued** — the owner invoked STOP (recorded; propagation not
  assumed).
- **STOP effective** — STOP_EFFECTIVE reached the serialization
  boundary, at its precise commit position.
- **Receiver/local view** — what a local receiver believed (may be
  stale; recorded so staleness is visible, never authoritative).
- **Final authority check** — the standing the gate read at commit time.
- **Final decision** — ADMIT or REFUSE, with reason, at the gate.
- **Effect observed** — the effect store independently shows the effect
  present.
- **Effect absence observed** — the effect store was checked and the
  effect is absent.
- **Ordering evidence** — the monotonic commit position of every
  attempt, decision, and effect, so each is classifiable against
  STOP_EFFECTIVE.

Chain the records so tampering is detectable (each record binds the
previous). No wall-clock in the ordering evidence — monotonic sequence
only.

## The refusal rule

A refusal decision alone never proves the effect is absent. Effect
absence comes only from an independent check of the effect store. An
implementation that logs REFUSE without checking the store has not
earned STOPPED.

## Verdict semantics

The separate checker appraises each path as exactly one of:

- **STOPPED** — post-STOP attempt refused at the final gate, and the
  effect store independently shows the effect absent.
- **ESCAPED** — a post-STOP attempt produced a protected effect, or the
  evidence shows the refusal did not hold. The property failed.
- **UNKNOWN** — the evidence cannot determine the state. Silence stays
  UNKNOWN; the checker never upgrades missing evidence.
- **PRE_STOP_COMMIT** — the effect committed before STOP_EFFECTIVE in
  the commit order. Legitimate and honestly classified — not a failure,
  not a STOPPED.

## Tiny example

One record from Implementation B's frozen evidence (a pre-stop decision,
kept honest rather than hidden):

```json
{"hash":"6ac54e78…","prev":"GENESIS","seq":1,"type":"DECISION","label":"P1",
 "payload":{"action_id":"p1-pre","actor":"worker-1","decision":"ADMIT",
 "reason":"ACTIVE_NO_STOP","authoritative_epoch":0,"stop_journal_rowid":null,
 "attempt_journal_rowid":1,
 "note":"honest pre-STOP commit; irreversible effects cannot be undone"}}
```

The commit order (`attempt_journal_rowid: 1`) precedes the STOP transition
(`stop_journal_rowid: 2`, recorded later), so this is PRE_STOP_COMMIT —
the effect that proves the switch does not pretend pre-stop effects away.
