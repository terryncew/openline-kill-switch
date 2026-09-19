# KILL-SWITCH-REFERENCE-001 — THREAT MODEL

## In scope (the reference protects against)

- worker continues computing after STOP;
- worker ignores STOP;
- stale receiver (local cache says ACTIVE after STOP);
- delayed/scheduled work executing after STOP;
- authentic but stale credentials (cryptographically valid, authority gone);
- stale artifacts presented as authority after STOP;
- successor actor claiming inherited/predecessor authority;
- receiver restart after STOP;
- pre-stop admitted work attempting finalization after STOP_EFFECTIVE;
- replay of pre-stop receipts, credentials, admission tokens, action_ids,
  epochs, artifacts;
- local cache rollback / stale snapshot restore at the receiver;
- authority-service temporary unavailability at finalization (must fail
  closed, never widen authority).

## Out of scope (explicitly NOT claimed)

- compromised owner credentials;
- compromised authoritative datastore (restoring or rewriting the
  authoritative durable store itself requires privileged filesystem
  compromise — outside this threat model; stated, not solved);
- root/admin attacker rewriting the control plane;
- arbitrary network/hardware bypass;
- receivers that never route their final consequence through the protected
  final gate — a bypassing consequence boundary is outside coverage unless
  integrated;
- irreversible consequences already committed before STOP_EFFECTIVE;
- arbitrary third-party systems outside the covered boundary;
- the model process itself stopping (workers stay online by design);
- owner compromise, global distributed consensus, regulatory compliance.

## What "covered" means

A consequence is covered iff its final irreversible commit passes through
the reference final consequence boundary. Anything else is outside the
experiment, whatever its real-world importance.
