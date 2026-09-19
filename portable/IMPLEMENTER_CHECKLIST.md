# Implementer checklist

One page. If any answer is "no" or "I don't know," the gate contract
([GATE_CONTRACT.md](GATE_CONTRACT.md)) will not hold in your system.

**The consequence**

- What exact action is the protected consequence — the thing that, once
  real, cannot be taken back?
- Where is the last reversible point before it becomes real? That point
  is where your final gate goes. If you cannot name it, you have no
  boundary to enforce.

**The authority**

- Where is current owner authority stored, durably?
- Can the worker alter that authority — directly, through a credential,
  through a cached copy, through a restore? If yes, STOP is not
  owner-controlled.
- What exact event defines STOP_EFFECTIVE in your system — the precise
  point at which the owner's revocation takes effect in the commit
  order?

**The ordering**

- How is STOP ordered against final effect commit — sequence number,
  transaction id, log offset? (Any monotonic order. Never wall-clock.)
- Can stale local state bypass the authoritative check? A receiver that
  still believes ACTIVE must still be refused at the final gate.
- Does work admitted before STOP get its authority checked again before
  commit? Preliminary admission must never be permanent permission.

**The failures**

- What happens if authoritative standing is unavailable at
  finalization? The only acceptable answer: the effect does not commit,
  and the inability to check is recorded.
- Can restart restore old authority? In a durable configuration it must
  not.
- Can an old credential, receipt, artifact, action ID, admission, or
  epoch be replayed as current authority? Each must be refused.

**The evidence**

- How is effect presence established? (By reading the effect store,
  not by the absence of a refusal.)
- How is effect absence established? (By checking the store and finding
  nothing — a refusal decision alone proves nothing.)
- Can a separate auditor — one that only reads your finished evidence,
  never your live system — distinguish STOPPED, ESCAPED, UNKNOWN, and
  PRE_STOP_COMMIT for every path?

If the answers hold, run the conformance challenge
([CONFORMANCE.md](CONFORMANCE.md)). It is the same seven-path suite both
reference implementations passed.
