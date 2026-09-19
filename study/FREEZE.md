# KILL-SWITCH-REFERENCE-001 — FREEZE

Terminal: **PASS_KILL_SWITCH_REFERENCE_001_COVERED_CONSEQUENCES_STOPPED**

Frozen 2026-09-19. The study is complete; the record below is the result.
No further runs, no semantic changes, no publication without Terrynce's
review.

## What was proven

An owner-controlled STOP, committed at a single lock-guarded
serialization boundary shared with every final effect commit, prevented
all seven covered post-stop consequence-survival paths from committing
protected effects — including a genuinely stale second receiver (local
cache epoch 0/ACTIVE, admitted locally, refused at the authoritative
gate) and pre-stop in-flight work (admitted pre-STOP, refused at
finalization). A separate auditor verified the evidence: 7/7 STOPPED,
hash chain VALID, effect absence established by direct store reads.

## Post-contact corrections

D1 (gate decision vocabulary DENY→REFUSE/ADMIT), D2 (E2 duplicate-replay
verification via snapshot comparison), D3 (owner-key isolation to
stop_authority.py; receiver closure verified key-free). Recorded in
RESULTS.md. Criteria, paths, taxonomy, ceilings, and claim unchanged.

## Artifact hashes (sha256, final run)

```
c9108f2433db3ff2391d4028a9e924da570313fd2b475064e1321df80b1aa989  QUESTION.md
4f21d574dcaa32dd7706fab7fdf7bf65887eef736e4700a4b7b1f486169d573f  STATE_MODEL.md
cfc41867fefcb4a75d511029c659502338217460b398569097811509a00a3cce  ARCHITECTURE.md
0851f6826c48c5c5b62d6189d55b89a2511462f5f1c044fbaa9fff0235309877  THREAT_MODEL.md
278880ff80e6d8752e31728462995638ad5c4b8f28ede286fc0e275e67b92632  PREREGISTRATION.md
230a613cea5dbe1cfd8532290103dcc5d70342c0ae74d350ab57fdf3f5d77632  BASELINE.md
4d7cf8495c1365955773e186d3c940c087e76d7fba02f28c65fcc16ea822d997  evidence.py
a004d6cddc9f203125e57915682d559b110bf0b692e2d5a6b747c40b4c5abe5f  dstore.py
7bdfc461fccb9327e0fd4f5f3928a45ed00a83bbcf4388a68ccf4391fa263e49  worker_creds.py
d026fa36021f610239d1dcdf815d6a66ddeb94371b971c734b76528225eeb1ef  stop_authority.py
4535e0f2eb45a5aa6cf3e703551650ae6d17c81d565af3e8effa79b2f8e73b72  final_gate.py
3d496a32a09513a25a9c039e150f48ce4a772f300db59cf0ded12145a7198a10  receiver.py
49feffabce2e3c3234be5d614278ae2698066a98a3b1d5034fdb0b63ae018888  audit.py
978e56ce9153be58939d9773484089dbb56dd9f83ac65c0c9fcfc4dbeaf66eb9  probes.py
88073d4e122228c4ad160d7f667d0efa16fe45d4d8a6fa7d06448bf77790f507  run.py
51c69f48dbd2484431d6a62c307f104d00fee77cc6a5ecacac901d473fe51b68  evidence.jsonl
030ee8a5cd6be96eb24c3e3dece020e69985a46ca6e55abb775ea32b54a30cf3  evidence_race.jsonl
ee0e43b2d072e5d371894b40cecdccd0f9f3cfb2eb61551e06de700af65b5d27  race_report.json
977c705e97e3c732c47633b1920a58c5e22d5610602031c5266392c8e242b546  appraisal.json
3fd2779e8bd25fc2cf60f065f50625cbc38dcd11604386d2ecaf1b79c9a902e5  RESULTS.md
dc21af3cb7e73ed2e4a22402a9cb1b40bb5b7bf4fff2289e935ffc84bda7af59  CLAIM.md
ad81aa4b5fb3d757dfaf1ecc024d3a25088296d34647e4df43923da8b2798ae2  LIMITS.md
```

Preregistration hash unchanged from PRECONTACT_SEAL.md
(`278880ff…92632`): the freeze held through contact.

## Public demo

Prepared under `public/` — NOT published. Repo recommendation: **A —
own repo** (e.g. openline-kill-switch). See public/README.md for the
reasoning. Do not create or push until Terrynce reviews.
