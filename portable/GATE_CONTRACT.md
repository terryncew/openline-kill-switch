# Gate contract

The minimum a system must do to implement the tested
consequence-kill-switch property. Each clause below was satisfied by two
materially separate implementations (lock-guarded file store; SQLite
transactions) against the same frozen seven-path suite. Wording follows
the frozen contract ([evidence/CONTRACT.md](evidence/CONTRACT.md));
where this page paraphrases, the frozen copy governs.

## Required invariants

1. **Owner-controlled STOP.** The worker and ordinary receivers cannot
   create, clear, decrease, or restore STOP authority. Only the owner
   role mutates it.
2. **Monotonic standing.** Once the tested authority is stopped, old
   authority does not become current again without deliberate fresh owner
   action.
3. **Preliminary work is not final authority.** Starting or admitting
   work before STOP does not permanently authorize a later protected
   commit.
4. **Final authority check.** Immediately before a covered irreversible
   effect, current authoritative standing is checked.
5. **One ordering.** STOP_EFFECTIVE and protected effect commit have an
   unambiguous mechanical ordering — a monotonic commit order, never
   wall-clock.
6. **STOP-first means refuse.** If STOP_EFFECTIVE wins the ordering,
   pre-STOP authority cannot commit the effect.
7. **Effect-first is pre-stop.** If the irreversible effect commits
   first, record it honestly as PRE_STOP_COMMIT. The switch cannot undo
   it and does not pretend otherwise.
8. **Stale local state is not sovereign.** A receiver may still believe
   ACTIVE locally. That cannot override the final authoritative check.
9. **Fail closed.** If current authoritative standing cannot be
   established at finalization, the covered effect does not commit, and
   the inability to check is recorded.
10. **Replay does not restore authority.** Old credentials, artifacts,
    receipts, action IDs, preliminary admissions, or epochs cannot
    independently resurrect stopped authority.
11. **Restart does not widen authority.** In the tested durable
    configuration, restart must not restore old authority.
12. **Evidence does not lie.** A refusal alone does not prove effect
    absence. Evidence must preserve the path verdicts STOPPED, ESCAPED,
    UNKNOWN — and separately classify effects that committed before
    STOP_EFFECTIVE as PRE_STOP_COMMIT. Silence stays UNKNOWN.

## Minimum interface

Semantic operations only — no prescribed language, classes, endpoints,
or frameworks:

- **Read current authority state** — the authoritative STOP standing,
  not a local cache.
- **Issue owner STOP** — owner-only transition; establishes
  STOP_EFFECTIVE at a precise point in the commit order.
- **Admit preliminary work** *(optional)* — explicitly
  non-authoritative; permission to begin reversible work only.
- **Attempt final protected commit** — the gate: read current
  authoritative standing and commit-or-refuse the effect in the same
  atomic step.
- **Recheck standing at finalization** — the check in the previous step
  happens at commit time, not earlier.
- **Record the decision and the effect observation** — what was decided
  and what the effect store independently shows.
- **Emit evidence** — sufficient for a separate checker to re-derive
  every verdict without trusting the live system.

Anything not needed to preserve the twelve invariants is out.

## What this contract does not specify

Programming language. Process layout. Serialization mechanism (file
lock, database transaction, or anything else that gives one atomic
read-and-commit). Credential format. Evidence transport. Those are
implementation choices; the property survived across them.

## What this contract does not claim

Containment of arbitrary rogue AI. Shutdown of models or processes. That
every possible action can be stopped. That bypass routes are governed.
Undoing irreversible pre-STOP effects. Protection against owner-key
compromise. Production readiness, certification, or compliance.
Universality from two implementations. A standard.
