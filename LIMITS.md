# LIMITS

The five strongest things this does not solve:

1. **Bypassing receivers.** A consequence is covered only if its final
   commit passes through the reference final gate. Any receiver, tool, or
   system that routes around the gate is outside coverage. The switch
   governs the boundary it is integrated with, nothing else.
2. **Pre-STOP_EFFECTIVE irreversibility.** Effects committed before the
   linearization point are pre-stop effects. The switch cannot undo them,
   and does not try. P1-step1 in the evidence is the honest example.
3. **The authoritative store itself.** Durability and the single ordering
   rest on one file. Restoring or rewriting that file with privileged
   filesystem access defeats the control; that attacker is outside the
   threat model. Stated, not solved.
4. **Owner compromise.** Whoever holds the owner credential can STOP — and
   can also advance epochs. The reference authenticates the role; it does
   not protect the role's key. Labeled HMAC stand-in throughout: the tested
   property is revocation observation and commit ordering, not signature
   strength.
5. **The model keeps running.** Workers stay online and capable by design.
   "Verifiable AI consequence kill switch" means old authority stopped
   working at covered boundaries — not that any process was turned off,
   and not that AI anywhere was shut down.

Also out of scope: compromised datastores, root/admin attackers rewriting
the control plane, network/hardware bypass, third-party systems outside
the covered boundary, regulatory compliance or certification, production
readiness, distributed consensus. Single-machine reference: the shared
serialization is a lock-guarded file store, not a distributed protocol.
Twenty race trials expose obvious race defects; they are not a safety proof.
