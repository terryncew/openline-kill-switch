# Portable consequence gate

The kill switch in this repository is a boundary rule, not a Python
dependency. This package states the rule in implementation-neutral terms,
so another system can implement it without copying this repository's
source.

One paragraph: put every covered consequence behind one final gate that
rechecks current owner authority in the same atomic step that commits or
refuses the effect. Give the owner's STOP a precise effective point in
your commit order. If STOP wins the ordering, pre-STOP authority cannot
commit the effect. If the effect committed first, record it honestly as
pre-stop. Fail closed when authority state is unavailable. Emit evidence
a separate checker can re-derive.

## What traveled

The property above was reproduced by two materially separate reference
implementations against the same frozen seven-path qualification
contract and evidence semantics
([GATE_CONTRACT.md](GATE_CONTRACT.md), frozen copy in
[evidence/CONTRACT.md](evidence/CONTRACT.md)):

- **Implementation A** — this repository, tag `v0.1.0` (commit
  `ebf2522`). Lock-guarded file store. Evidence in `evidence/frozen/`.
- **Implementation B** — Python 3.12 stdlib + SQLite 3.45.1
  transactions. Built from the frozen contract alone; the v0.1.0 source
  tree was never opened during construction. As-built source in
  [impl-b/](impl-b/); frozen evidence in
  [evidence/impl-b-evidence.jsonl](evidence/impl-b-evidence.jsonl)
  (auditor appraisal:
  [evidence/impl-b-auditor-appraisal.txt](evidence/impl-b-auditor-appraisal.txt)).

Two implementations do not prove every technology can satisfy the
contract. The bounded public meaning: the tested property traveled once
across a materially separate implementation boundary. Full results:
[evidence/RESULTS.md](evidence/RESULTS.md).

## The package

- [GATE_CONTRACT.md](GATE_CONTRACT.md) — the required invariants and the
  minimum semantic interface. Semantics, not code structure.
- [IMPLEMENTER_CHECKLIST.md](IMPLEMENTER_CHECKLIST.md) — one page: does
  your system have the right shape?
- [CONFORMANCE.md](CONFORMANCE.md) — the seven-path challenge, PASS
  semantics, and what passing does not mean.
- [EVIDENCE.md](EVIDENCE.md) — the minimum evidence a separate checker
  needs to re-derive every verdict.
- [evidence/](evidence/) — the frozen contract, criteria, and both
  implementations' evidence, byte-for-byte with hashes.
- [impl-b/](impl-b/) — Implementation B as built, runnable.

Start with the checklist. If your system cannot answer its questions,
the contract will not hold there either.
