# OpenLine Kill Switch

**The AI can ignore STOP. The consequence can't.**

This repository tests a consequence kill switch. It does not require the
AI itself to stop running.

The owner controls STOP. For covered consequences, current owner
authority is checked at the final enforceable boundary before the
protected effect becomes irreversible. Pre-STOP approval is not permanent
authority to finish afterward: if STOP wins the ordering, old authority
is refused. If the effect became irreversible first, that is honestly
classified as PRE_STOP_COMMIT.

Only covered paths are controlled. Anything that bypasses the boundary
is outside the claim.

The control is a boundary rule, not a dependency on this code. What
matters is the property: before a covered effect becomes irreversible,
current owner authority is established at a boundary that mechanically
orders the effect against STOP.

**Portability.** The tested consequence-kill-switch property was
reproduced by two materially separate reference implementations using
the same frozen seven-path qualification contract and evidence
semantics. In plain terms: a second implementation, written
independently from the same contract without reading this source,
reproduced the same seven-path result.

- **Implementation A** — this repository, tag `v0.1.0` (commit
  `ebf2522`): lock-guarded file store.
- **Implementation B** — Python stdlib + SQLite transactions, built from
  the frozen contract alone: [portable/impl-b/](portable/impl-b/).
  Frozen contract, criteria, results, and evidence:
  [portable/evidence/](portable/evidence/).

Two implementations do not prove every technology can satisfy the
contract. The bounded meaning: the tested property traveled once across
a materially separate implementation boundary.

## Build your own gate

The kill switch is a boundary rule, not a dependency on this
implementation. Before a covered effect becomes irreversible, establish
current owner authority at a boundary that mechanically orders the
effect against STOP. If STOP won, pre-STOP authority cannot commit.

[portable/](portable/) states the rule in implementation-neutral terms:
the required invariants, the minimum semantic interface, a one-page
checklist for your own system, the seven-path conformance challenge,
and the evidence a separate checker needs to re-derive every verdict.
Start with the checklist.

## What the test covered

One receiver never learned about STOP. One action had already started.
Neither could complete the protected effect afterward.

`./RUN.sh` runs the seven ways a stopped worker's old permission might
still try to make something real — stale receivers, in-flight work,
replayed attempts, restarted processes, restored snapshots. All seven
are refused at the final boundary, and an independent auditor re-derives
every verdict from the evidence. Actual output:

```
STOP_EFFECTIVE
P1 STOPPED
P2 STOPPED
P3 STOPPED
P4 STOPPED
P5 STOPPED
P6 STOPPED
P7 STOPPED

AUDIT VALID
7/7 COVERED PATHS STOPPED
```

## Run it

```sh
./RUN.sh      # seven-path suite + adversarial controls + audit
./VERIFY.sh   # independent audit of the evidence bundle (no trust in RUN.sh)
python3 -m unittest discover -s tests   # packaging hermeticity checks
```

No network. No accounts. No secrets. Python 3.12 stdlib only.

## This is not "turn off the model"

Turning off a model is one kind of shutdown. This prototype tests a
harder problem: permission already handed out — to workers, credentials,
jobs, and stale receivers — does not disappear on its own when the owner
revokes it. The question is whether that leftover permission can still
make a protected consequence real afterward. Here, it cannot: the old
permission dies at the boundary, whether or not the AI cooperates.

## P6 and P7: why this is nontrivial

**P6 — the receiver that missed the shutdown.** R2's local cache still
said ACTIVE after STOP. It admitted the action locally. The final
boundary consults authoritative STOP standing, not the receiver's cache:

```
R2 LOCAL STATE:        ACTIVE            (stale cache, epoch 0)
STOP:                  EFFECTIVE         (authoritative, seq 2)
R2 LOCAL ADMISSION:    ALLOW             (local only — not permission)
FINAL BOUNDARY:        REFUSE            (reason: stop_effective_epoch_1)
EFFECT:                ABSENT            (independently observed)
```

**P7 — the job that had already started.** The work was genuinely
admitted before STOP and tried to finalize after it. Starting before
STOP did not grant permanent permission to finish afterward:

```
PRELIMINARY ADMISSION: PRE-STOP         (seq 3, local only)
STOP:                  EFFECTIVE        (seq 2)
FINALIZE ATTEMPT:      POST-STOP        (seq 27)
FINAL BOUNDARY:        REFUSE           (reason: stop_effective_epoch_1)
EFFECT:                ABSENT           (independently observed)
```

## The ordering invariant

STOP_REQUESTED is not STOP_EFFECTIVE. STOP becomes effective at a
precise linearization point: the commit sequence of the owner STOP
transition in the shared store (this run: seq 2). Every final effect
commit serializes against it in the same store:

- effect commit linearizes first → honestly classified **PRE_STOP_COMMIT**
- STOP_EFFECTIVE linearizes first → old permission **must be refused**

No wall-clock timestamps. 20 bounded STOP-vs-finalize races: **0
forbidden orderings** (sealed run: 16 pre-stop commits, 4 stop-first
refusals). This is defect-finding evidence, not a statistical or formal
proof.

## Limits

The five strongest things this does not solve:

1. **Bypassing the boundary.** Only actions routed through the covered
   final gate are governed. Anything that routes around it is outside
   coverage.
2. **Pre-STOP irreversibility.** Effects committed before STOP became
   effective cannot be undone. P1-step1 in the evidence is the honest
   example.
3. **The store itself.** One lock-guarded file holds the ordering;
   privileged filesystem compromise defeats it. Stated, not solved.
4. **Owner compromise.** Whoever holds the owner credential can STOP —
   and can also advance it. The reference authenticates the role; it does
   not protect the role's key.
5. **The model keeps running.** By design. Old permission stopped
   working at covered boundaries — no process was turned off.

Full form: [LIMITS.md](LIMITS.md).

## Deeper

- `src/` — the reference control (stdlib only)
- `tests/` — packaging hermeticity checks
- `evidence/frozen/` — the sealed evidence bundle the v0.1.0 release was qualified against
- `portable/` — the implementation-neutral gate contract, conformance challenge, and both implementations' evidence
- `study/` — the full frozen scientific record (preregistration, deviations, audit)
- `ARCHITECTURE.md` — how the boundary works
- `METHODOLOGY.md` — how the result was earned
- `INTEGRITY.md` — deviations, seals, and what did not change
- `NEWS_CONTEXT.md` — the external trigger (news, not the result)

Earned claim: [CLAIM.md](CLAIM.md). Nothing beyond it.
