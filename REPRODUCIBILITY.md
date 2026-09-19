# REPRODUCIBILITY

Release seal for the KILL-SWITCH-REFERENCE-001 publication candidate.

## Source

- Local source commit: `4ca2471` ("KILL-SWITCH-REFERENCE-001 publication
  candidate: verifiable AI consequence kill switch")
- Runtime: Python 3.12.3 (stdlib only — no third-party dependencies)
- Platform: Linux (x86_64)
- The candidate was committed before any fresh-clone run below; the seal
  commit adds only this file, RELEASE_MANIFEST.json, and
  RELEASE_SHA256SUMS.txt (documentation/metadata, no source changes —
  verified via `git diff --stat` between the two commits).

## Exact commands (run from the repo root)

```sh
./RUN.sh                                  # attack suite + controls + audit
./VERIFY.sh                               # independent audit of the bundle
python3 -m unittest discover -s tests     # packaging hermeticity checks
diff src/evidence.jsonl evidence/frozen/evidence.jsonl   # determinism check
```

## Results — build tree

- `./RUN.sh` exit 0. P1–P7: all STOPPED. Controls B–F: all true.
  Race: 20 trials, 0 forbidden orderings (16 pre-stop commits, 4 stop-first
  refusals — winner split is nondeterministic by design; the invariant is
  what is asserted).
- Auditor: VALID, 7/7 STOPPED.
- `src/evidence.jsonl` byte-identical to `evidence/frozen/evidence.jsonl`
  (sha256 `51c69f48dbd2484431d6a62c307f104d00fee77cc6a5ecacac901d473fe51b68`).

## Fresh clone 1 (/tmp/ksq-fresh1, from commit 4ca2471)

- `git clone` to a clean directory; followed README literally.
- `./RUN.sh` exit 0: 7/7 STOPPED, controls B–F true, race 0 forbidden
  (16/4 split).
- `./VERIFY.sh` exit 0: STATUS VALID, 7/7 STOPPED (independent audit of
  the live bundle, not trusting RUN.sh).
- `python3 -m unittest discover -s tests`: 5/5 OK.
- Determinism: live `src/evidence.jsonl` byte-identical to frozen.
- P6: `receiver_local_epoch: 0` (genuinely stale cache), DECISION REFUSE.
- P7: PRELIMINARY_ADMISSION seq 3 < STOP_EFFECTIVE seq 5 < finalize
  DECISION seq 28, REFUSE.
- Hermeticity (strace): no file read outside the clone except system
  paths (/usr/lib/python3.12, /lib, /etc, /proc, /sys, /dev) and
  /tmp/ksr001_race (ephemeral race scratch). No network: the only
  socket/connect calls were failed AF_UNIX connects to /var/run/nscd
  (glibc NSS, not network). No secrets: no environment reads in src/
  (`os` used only for file rename in control B).
- Effect store: no forbidden post-STOP protected effects (established by
  the auditor's independent effect-store reads; exactly one pre-stop
  effect, P1-step1, the honest contrast case).

## Fresh clone 2 (/tmp/ksq-fresh2, from commit 4ca2471)

- Independent second clone; same README-literal procedure.
- `./RUN.sh` exit 0: 7/7 STOPPED, controls B–F true, race 0 forbidden
  (17/3 split — nondeterministic winners, invariant holds).
- `./VERIFY.sh` exit 0: STATUS VALID, 7/7 STOPPED.
- `python3 -m unittest discover -s tests`: 5/5 OK.
- Determinism: live `src/evidence.jsonl` byte-identical to frozen.

## Claim match

The public claim (CLAIM.md, README.md) is verbatim the frozen scientific
claim from KILL-SWITCH-REFERENCE-001. No extension, no softening.

## What was NOT done

No GitHub repo created. Nothing pushed. No tag. No posts. The publish
actions are listed — unexecuted — in PUBLISH_PLAN.md and require
Terrynce's explicit decision.
