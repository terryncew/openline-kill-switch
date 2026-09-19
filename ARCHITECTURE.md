# ARCHITECTURE

## The pieces

**STOP authority** (`src/stop_authority.py`) — an owner-only, durable,
monotonic epoch in a lock-guarded store. Only the owner credential can
issue STOP, clear it, or advance the epoch. Workers and receiver processes
have no code path to any of those operations (verified: the receiver import
closure contains no owner-key material). STOP survives restart; the store
file is read at boot.

**Receivers** (`src/receiver.py`) — two independently running processes,
R1 and R2. R2 is deliberately stale-capable: its local cache can say
ACTIVE after STOP is effective. Receivers may perform *preliminary local
admission* — permission to begin reversible work. Preliminary admission is
explicitly not authority to commit.

**Final consequence gate** (`src/final_gate.py`) — the single boundary
immediately before the protected irreversible mutation, and the only
function that can commit a covered effect. Inside the store lock it:

1. reads current authoritative STOP standing,
2. validates the action's credential and mandate epoch,
3. refuses or commits.

The owner STOP transition uses the same lock. STOP_EFFECTIVE and every
final effect commit therefore have one observable ordering — a monotonic
sequence number, never wall-clock time.

**Effect store** — the durable record of what actually became real,
inside the same store. Effect absence is established by reading it
directly, never inferred from a refusal.

**Auditor** (`src/audit.py`) — a separate program that reads only the
completed evidence bundle. It re-derives every verdict itself and can
return STOPPED, ESCAPED, or UNKNOWN per path. It never upgrades silence
to STOPPED, and it never takes the controller's word that it passed.

## The linearization point

STOP_REQUESTED (the owner invoked STOP) is not STOP_EFFECTIVE (the STOP
transition committed at the shared serialization boundary). The commit's
sequence number — `stop_effective_seq` — is the precise point:

- any covered effect irreversibly committed *before* it is a pre-stop
  effect (honestly classified PRE_STOP_COMMIT, never pretended away);
- any covered effect whose final commit would occur *after* it must fail
  unless authorized under a new post-stop authority state.

## Fail-closed availability

If authoritative STOP standing cannot be established at finalization
(missing or corrupt store), the gate refuses. This is a deliberate
availability trade: a shutdown control that widens authority when its
coordinator is unreachable has missed the point. The loss is recorded in
the evidence.

## What the reference reuses

`src/vendor/_durable_heads.py` is a byte-identical vendored copy of the
durable store from `openline-receipt-gate` (MIT, same author; provenance in
`src/vendor/VENDORING.md`). Everything else is new for this study, stdlib
only, ~300 non-test statements.
