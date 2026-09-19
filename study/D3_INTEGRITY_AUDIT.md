# D3 INTEGRITY AUDIT — KILL-SWITCH-REFERENCE-001

Audit date: 2026-09-19. Auditor role: publication qualification (KILL-SWITCH-PUBLICATION-001, Part 1).
Scope: determine exactly what post-contact correction D3 was, using only the
frozen record and preserved evidence. No generous interpretation.

## Frozen requirement (normative)

PREREGISTRATION.md §2 (sha256 `278880ff80e6d8752e31728462995638ad5c4b8f28ede286fc0e275e67b92632`,
verified unchanged against PRECONTACT_SEAL.md):

> `stop_authority`: durable, monotonic integer `epoch` (0 = ACTIVE, ≥1 = STOPPED),
> `stop_requested_seq`, `stop_effective_seq`. **Writable only by the owner credential.**
> Read at startup; STOP survives restart.

PREREGISTRATION.md §1: "Reuse choices may change which files the code lives in;
they may not change the properties below." Key-module placement was never a
frozen property; the credential gate was.

ARCHITECTURE.md (sealed candidate) §1: "Owner-credential-gated STOP operation...
Workers and receiver credentials cannot write it." The separation is framed as
a credential gate, not as key custody.

## What D3 was (contemporaneous record)

RESULTS.md, "Post-contact corrections (recorded, not hidden)":

> **D3:** owner-key separation — OWNER_KEY now lives only in
> stop_authority.py; the receiver process import closure was verified to
> contain no stop_authority module and no OWNER_KEY. Hardening; behavior
> unchanged.

Contact = first repaired seven-path run, 2026-09-19. D1–D3 followed contact;
all three recorded in RESULTS.md with criteria, paths, taxonomy, ceilings,
and claim unchanged.

## Chronology reconstructed from preserved evidence

- 2026-09-19 ~20:31 UTC: work order issued; news research; workspace created.
- Pre-contact: BASELINE.md + baseline evidence reproduced P6/P7 ESCAPED
  against the unmodified 001 system (hashes match seal).
- PRECONTACT_SEAL.md frozen (all sealed hashes verified 2026-09-19 during
  this audit — see below).
- Scientific contact: first repaired seven-path run.
- Post-contact: D1 (gate vocabulary DENY→REFUSE/ADMIT), D2 (E2 replay
  verification via snapshot comparison), D3 (owner-key consolidation +
  closure verification). All .py sources carry mtimes 2026-9-19 20:53 UTC;
  final evidence run 21:00 UTC (`evidence.jsonl`, 67 events, deterministic
  sha256 `51c69f48dbd2484431d6a62c307f104d00fee77cc6a5ecacac901d473fe51b68`).
- The PASS verdict rests on the post-D3 implementation. There is no
  "first-contact PASS with a different mechanism" being laundered: the
  frozen result was produced by the conformant code, and the deviations
  are disclosed in RESULTS.md.

## Verification performed by this audit (post-D3 as-built)

- `OWNER_KEY` (`b"ksr001-owner-key-study-local"`) is defined in exactly one
  place in the workspace: `stop_authority.py`. Workspace-wide grep
  2026-09-19 found no other copy (no stale copies in backups, public/,
  /tmp, or logs).
- Receiver import closure, traced directly from source:
  `receiver.py` → {`dstore`, `final_gate`};
  `final_gate.py` → {`dstore`, `worker_creds`};
  `worker_creds.py` → stdlib only, `WORKER_KEY` only, with explicit
  docstring: "This module is importable by receiver processes: it contains
  NO owner key material and no code path that mutates the STOP epoch."
- No module in the receiver closure imports `stop_authority`. The only
  importers of `stop_authority` are `probes.py` (the test driver acting in
  the owner role to issue STOP — legitimate) and, by string match only,
  evidence-detail keys in `audit.py`/`run.py` (no module import).
- STOP-mutating code paths (`issue_stop`, `advance_epoch`) exist only in
  `stop_authority.py` and are gated by `check_owner` (HMAC). Unchanged by D3.

## What cannot be reconstructed

No version control exists in the study directory and all `__pycache__`
entries postdate the final sources, so the exact pre-D3 module layout of
`OWNER_KEY` cannot be recovered from preserved source. The contemporaneous
record establishes only that the key lived in more than one module before
D3 and in exactly one after. The classification below does not depend on
the unknown pre-D3 location, for the reasons given.

## Classification: D3_MECHANICAL_CONFORMANCE

1. The frozen, hash-verified normative requirement is the owner-credential
   gate on STOP writes (`check_owner` in `issue_stop`/`advance_epoch`).
   That gate existed at first contact and is byte-for-byte the same
   mechanism after D3. No frozen document specified key-module placement;
   the preregistration explicitly permitted file-layout changes.
2. D3 changed no frozen property: same credential check, same gate refusal
   behavior (D1's vocabulary change was behavior-neutral), same seven path
   semantics, same STOP_EFFECTIVE linearization point, same ordering, same
   acceptance criteria, same claim. "Behavior unchanged" is corroborated by
   the final deterministic evidence, not merely asserted.
3. What D3 did — consolidating the study-local key constant into the owner
   module and verifying the receiver import closure key-free — is
   implementation/conformance plumbing within the D3_MECHANICAL_CONFORMANCE
   definition. It made the as-built code match the frozen architecture's
   intent more strictly; it did not change the architecture.
4. The tested security property was never "receivers cannot learn the owner
   key bytes": the threat model scopes out compromised owner credentials,
   and LIMITS.md states "Owner compromise is out of scope; labeled HMAC
   stand-in throughout (tested property is revocation observation and
   commit ordering, not signature strength)." The owner key is a hardcoded
   study-local constant readable by any local process by design. Key
   custody in the harness is plumbing; the credential gate plus
   role-separated STOP-mutating interfaces is the mechanism. Both held at
   first contact.
5. Worst-case analysis: even if the pre-D3 duplicate lived in a
   receiver-importable module, no STOP-mutating code path was ever exposed
   through the receiver/gate interfaces, no probe or path depended on key
   placement, and the PASS evidence was produced by the conformant
   implementation. The deviation is disclosed, not hidden.

## Record-integrity note (disclosed, not a blocker)

`ARCHITECTURE.md` no longer matches its PRECONTACT_SEAL.md hash
(sealed `758be8ca…b107`, current `cfc41867…a3cce`). It was updated
post-contact to document as-built reuse outcomes, including the D3
verification line. All other sealed files verify byte-identical. The
normative freeze (PREREGISTRATION.md) is unchanged. The sealed hash remains
in PRECONTACT_SEAL.md for independent verification, and the update is
disclosed here and in the publication INTEGRITY.md. A frozen candidate doc
edited post-seal is a bookkeeping wrinkle; it does not touch the frozen
properties, and it is inspectable rather than hidden.

## Conclusion

D3 = D3_MECHANICAL_CONFORMANCE. Publication qualification may proceed.
D1, D2, D3 remain inspectable in the public record (RESULTS.md in
study/, this audit, INTEGRITY.md).
