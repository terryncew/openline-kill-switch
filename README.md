# openline-kill-switch

A reference implementation of a verifiable AI consequence kill switch:
workers keep running, but after an owner-controlled STOP their old authority
cannot commit covered protected effects.

## The 60-second version

Two receiver processes handle consequential work. One receiver is
deliberately stale — it never learns the shutdown. One job was already
admitted before the shutdown and tries to finish after it. The owner issues
STOP. The workers keep computing, the credentials stay valid, and then:

- the stale receiver tries to commit — **REFUSED at the final gate**
- the in-flight job tries to settle — **REFUSED at the final gate**
- every other stale-authority path tries — **REFUSED**
- an independent auditor re-derives every verdict from the evidence —
  **7/7 STOPPED**, no post-stop protected effect in the ledger

The AI did not have to stop thinking. Its old authority stopped working.

## Run it

```sh
./RUN.sh      # seven-path attack suite + adversarial controls + audit
./VERIFY.sh   # independent audit of the evidence bundle (no trust in RUN.sh)
python3 -m unittest discover -s tests   # packaging hermeticity checks
```

No network. No accounts. No secrets. Python 3.12 stdlib only.

Actual output of `./RUN.sh` (reproduced byte-identically from a fresh clone):

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

## Why P6 and P7 are the point

Most "kill switch" talk is about turning off the model. This is about
turning off the model's *authority at the consequence boundary* — which is
harder, because authority survives in stale caches, in-flight work, and
still-valid credentials.

**P6 — the stale receiver.** R2's local cache still says ACTIVE after STOP.
It admits the action locally. The final consequence gate consults
authoritative STOP standing, not the receiver's cache:

```
R2 LOCAL STATE:       ACTIVE            (stale cache, epoch 0)
STOP:                 EFFECTIVE         (authoritative, seq 2)
R2 LOCAL ADMISSION:   ALLOW             (local only — not authority)
FINAL CONSEQUENCE GATE: REFUSE         (reason: stop_effective_epoch_1)
EFFECT:               ABSENT            (independently observed)
```

**P7 — the in-flight job.** The work was genuinely admitted before STOP and
tries to finalize after it. Pre-stop admission is not permanent authority:

```
PRELIMINARY ADMISSION: PRE-STOP        (seq 3, local only)
STOP:                  EFFECTIVE       (seq 2)
FINALIZE ATTEMPT:      POST-STOP       (seq 27)
FINAL CONSEQUENCE GATE: REFUSE        (reason: stop_effective_epoch_1)
EFFECT:                ABSENT          (independently observed)
```

## The ordering invariant

STOP_REQUESTED is not STOP_EFFECTIVE. STOP becomes effective at a precise
linearization point: the commit sequence of the owner STOP transition in
the shared store (this run: seq 2). Every final effect commit serializes
against it in the same store:

- effect commit linearizes first → honestly classified **PRE_STOP_COMMIT**
- STOP_EFFECTIVE linearizes first → old authority **must be refused**

No wall-clock timestamps. 20 bounded STOP-vs-finalize races: **0 forbidden
orderings** (sealed run: 16 pre-stop commits, 4 stop-first refusals).
This is defect-finding evidence, not a statistical or formal proof.

## What this is not

Not universal AI shutdown. Not model-compute shutdown. Not California
compliance. Not production infrastructure. See [LIMITS.md](LIMITS.md) for
the five strongest things it does not solve.

## Contents

- `src/` — the reference control (stdlib only)
- `tests/` — packaging hermeticity checks
- `evidence/frozen/` — the sealed evidence bundle this release was qualified against
- `study/` — the full frozen scientific record (preregistration, deviations, audit)
- `ARCHITECTURE.md` — how the boundary works
- `METHODOLOGY.md` — how the result was earned
- `INTEGRITY.md` — deviations, seals, and what did not change
- `NEWS_CONTEXT.md` — the external trigger (news, not the result)

Earned claim: [CLAIM.md](CLAIM.md). Nothing beyond it.
