# OpenLine Kill Switch

**The AI can ignore STOP. The consequence can't.**

A reference kill switch for covered AI actions. The worker can keep
running, keep its credential, and have work already underway — but after
the owner hits STOP, its old permission can no longer make a covered
action real.

STOP does not shut the model down. It revokes the permission for an
AI-originated action to become a real protected consequence: a payment
sent, code deployed, protected data written, a credential issued, a job
finalized. The AI does not have to listen, because the control lives in
the environment, not the model — every covered action must pass a final
protected boundary, which checks current owner permission and refuses
anything revoked. Emergency control moves outside the AI: shutdown stops
depending on persuading, prompting, or terminating the worker.

The catch is real and stated up front: only consequences routed through
the covered boundary are controlled, and effects already irreversibly
committed before STOP cannot be undone. See [LIMITS.md](LIMITS.md).

## The weird part

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
- `study/` — the full frozen scientific record (preregistration, deviations, audit)
- `ARCHITECTURE.md` — how the boundary works
- `METHODOLOGY.md` — how the result was earned
- `INTEGRITY.md` — deviations, seals, and what did not change
- `NEWS_CONTEXT.md` — the external trigger (news, not the result)

Earned claim: [CLAIM.md](CLAIM.md). Nothing beyond it.
