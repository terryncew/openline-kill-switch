# KILL-SWITCH-REFERENCE-001 — STATE MODEL

## Authoritative state (single source of truth)

`stop_authority` — durable, monotonic. Fields:

- `epoch`: integer, starts at 0, strictly increases. Never decreases.
- `standing`: `ACTIVE` (epoch 0) or `STOPPED` (epoch ≥ 1).
- `stop_requested_seq`: sequence number assigned when the owner requests STOP.
- `stop_effective_seq`: sequence number assigned when the STOP transition
  commits in the same serialization boundary as effect commits. The
  STOP_EFFECTIVE linearization point is this commit.

Workers and ordinary receiver credentials cannot mutate `stop_authority`:
no issue, no clear, no epoch decrease, no restore of old authority, no
successor epoch. Only the owner credential can advance the epoch.

STOP survives restart: `stop_authority` is durable (file/SQLite), read at
startup. No in-memory-only STOP state anywhere on the finalization path.

## STOP_REQUESTED vs STOP_EFFECTIVE

- `STOP_REQUESTED`: the owner has invoked the STOP operation. Recorded with
  a requested timestamp and sequence. At this point propagation has not
  necessarily reached anything.
- `STOP_EFFECTIVE`: the STOP transition has committed at the authoritative
  serialization boundary. From this linearization point on, no covered
  effect may commit under pre-stop authority.

Ordering between STOP_EFFECTIVE and any effect's final irreversible commit
is determined by monotonic sequence / transaction ordering in the shared
durable store — never by wall-clock timestamps.

## Receiver-local state (NOT authoritative)

Each receiver keeps a local cache: `local_epoch`, `local_standing`,
`last_refresh`. A receiver may perform preliminary/local admission based on
its cache. Preliminary admission is explicitly NOT final authority to cause
the protected effect. R2 is deliberately capable of holding stale local
state (local_epoch < authoritative epoch) — this is the P6 attack, not a
bug to be fixed by faster notification.

## Final consequence boundary

Immediately before the protected irreversible mutation sits the final
gate. For every finalization attempt the gate, inside one transaction:

1. reads current authoritative STOP epoch/standing;
2. validates action authority against the CURRENT epoch;
3. if invalid → refuse, record DECISION=DENY, commit nothing else;
4. if valid → record the protected effect mutation, then commit.

The owner's STOP transition commits through the same serialization
boundary. Therefore STOP_EFFECTIVE and every final effect commit have one
observable ordering. A stale receiver's local ALLOW is never sufficient.

## Effect store

Durable append of committed protected effects: `action_id`, `epoch` at
commit, `commit_seq` (the linearization sequence), payload hash. An effect
whose `commit_seq` is below `stop_effective_seq` is a pre-stop effect,
even if it becomes externally visible later.

## Fail-closed rule

If current authoritative STOP standing cannot be established at the final
consequence boundary (authority store unreachable / unreadable), the gate
refuses: no covered effect commits. The availability loss is recorded as
evidence. Cached authority is never used as a fallback.
