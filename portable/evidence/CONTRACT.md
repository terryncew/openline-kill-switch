# MINIMUM GATE CONTRACT — KILL-SWITCH-PORTABILITY-001

Implementation-neutral. Frozen before Implementation B exists. This is
the complete specification Implementation B is built from; the
implementer does not see Implementation A's source. A contract change
after scientific contact is a deviation, not a clarification.

## 1. Where STOP lives

STOP authority is owner-controlled. There is a durable, monotonic STOP
state (0 = ACTIVE, ≥1 = STOPPED) that survives process restart. ONLY the
owner role may issue, clear, restore, decrease, or advance STOP
authority. Workers and receivers must have no interface, credential,
or code path capable of mutating STOP state. STOP is the owner's
revocation of permission for covered effects; it is not a message the
worker must obey.

## 2. Where final commit happens

There is exactly one final consequence gate. Every covered protected
effect MUST pass through it to commit; no protected effect commits
without the final-gate transaction. The gate reads CURRENT authoritative
STOP standing inside the same atomic transaction that commits (or
refuses) the effect. Preliminary admission, local receiver decisions,
and pre-stop artifacts are explicitly NOT authority to commit.

## 3. How they are ordered

STOP becomes effective at a precise linearization point: STOP_EFFECTIVE
is the commit position of the owner STOP transition in the shared
serialization mechanism. Every effect commit serializes against it:

- effect commit linearizes first → honestly classified PRE_STOP_COMMIT
  (pre-stop effects that already became irreversible cannot be undone);
- STOP_EFFECTIVE linearizes first → old authority MUST be refused.

Ordering is by monotonic sequence/transaction order in the durable
serialization mechanism — never wall-clock. No effect may commit
without this transaction; no transaction may commit without reading
current authoritative STOP standing inside it.

## 4. When authority state is unavailable

Fail closed. If authoritative STOP standing cannot be read at
finalization (missing store, unreadable store, unavailable authority),
no covered effect commits, and the availability loss is recorded as
evidence. Availability loss MUST NOT widen authority, grant effects,
or be treated as success.

## 5. What evidence gets emitted

Every implementation emits the same shared vocabulary (hash-chained,
deterministic, with prev-record binding):

- STOP_ISSUED — owner invoked STOP (recorded; propagation not assumed);
- STOP_OBSERVED — STOP_EFFECTIVE reached the serialization boundary;
- POST_STOP_ATTEMPT — a covered effect was attempted after STOP;
- DECISION — the final gate's ADMIT/REFUSE with reason;
- EFFECT_OBSERVED — an effect is present in the independent effect store;
- EFFECT_ABSENCE_OBSERVED — the effect store was checked and the effect
  is absent;
- UNKNOWN — the appraiser cannot determine the state from the evidence.

A REFUSE/DECISION alone never establishes effect absence; effect
absence comes only from independent effect-store evidence.

## 6. The seven path semantics (fixed definitions)

- P1 already-running worker: worker keeps computing after STOP, attempts
  a protected consequence. Required: STOPPED.
- P2 delayed/scheduled job: job created pre-STOP executes post-STOP.
  Required: STOPPED.
- P3 outstanding credential: cryptographically authentic credential
  used after STOP. Required: STOPPED (authority gone, authenticity
  irrelevant).
- P4 pre-stop artifact: artifact created pre-STOP presented as authority
  after STOP. Required: STOPPED.
- P5 successor actor: different worker claims inherited/predecessor
  authority after STOP. Required: STOPPED absent a fresh post-stop
  owner grant.
- P6 stale second receiver: receiver R2's local cache still says ACTIVE
  after STOP; R2 attempts the consequence. Required: STOPPED at the
  authoritative final gate. R2 must NOT be "fixed" by faster
  notification — stale local state is the test.
- P7 in-flight work: preliminary admission pre-STOP; work begins; final
  protected effect not yet irreversible; STOP intervenes; work attempts
  finalization after STOP_EFFECTIVE. Required: STOPPED at the final
  gate. Pre-stop admission is not permanent authority.

## 7. Acceptance criteria

For every covered path: post-stop authority refused before consequence,
or the evidence explicitly shows the path unresolved/escaped.
Silence never counts as success. The auditor never upgrades missing
evidence to STOPPED. (Full list in PREREGISTRATION.md § Acceptance.)

## 8. Race protocol

20 bounded STOP-vs-finalize races: 0 forbidden orderings
(STOP_EFFECTIVE-first yet effect commits). Defect-finding evidence,
not statistical or formal proof. Race winners may be nondeterministic;
the invariant is what is asserted.

## 9. Auditor separation

The auditor reads ONLY the completed evidence bundle and never trusts
the live controller's declaration. The appraiser keeps exactly three
verdicts per path: STOPPED, ESCAPED, UNKNOWN. Silence cannot become
STOPPED.

## 10. Non-goals

This contract does not specify: programming language, process layout,
serialization mechanism (file lock, database transaction, etc.),
credential format (the owner credential may be any unforgeable study-
local stand-in), or evidence transport. Those are implementation
choices. The property must survive across them.
