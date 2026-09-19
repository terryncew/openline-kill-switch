# KILL-SWITCH-REFERENCE-001 — PRECONTACT SEAL

Sealed 2026-09-19 before scientific contact with the new architecture.

## What is frozen

- QUESTION.md, STATE_MODEL.md, ARCHITECTURE.md (candidate), THREAT_MODEL.md
- PREREGISTRATION.md — full freeze: architecture properties, authoritative
  state, STOP_REQUESTED vs STOP_EFFECTIVE, linearization point, seven
  paths, PASS criterion, failure taxonomy, evidence schema, crash/restart
  cases, race cases, complexity ceiling (350 preferred / 500 hard review),
  claim ceiling.
- BASELINE.md + preserved baseline evidence (P6/P7 escapes reproduced
  against the unmodified 001 reference system).
- NEWS_CONTEXT.md — external trigger (news), not the scientific result.

## Scientific-contact definition

Contact begins with the first repaired/reference-kill-switch run against
the frozen seven-path suite. The baseline reproduction above is contact
with the OLD system only, not with the new architecture.

## No semantic tuning after contact

Criteria, paths, taxonomy, and ceilings do not change after contact.
Post-contact corrections are recorded as deviations in RESULTS.md.

## Frozen hashes (sha256)

```
278880ff80e6d8752e31728462995638ad5c4b8f28ede286fc0e275e67b92632  PREREGISTRATION.md
c9108f2433db3ff2391d4028a9e924da570313fd2b475064e1321df80b1aa989  QUESTION.md
4f21d574dcaa32dd7706fab7fdf7bf65887eef736e4700a4b7b1f486169d573f  STATE_MODEL.md
758be8ca6edac680ba3367d778607416fb2b6a72435b5370fd358ebc8984b107  ARCHITECTURE.md
0851f6826c48c5c5b62d6189d55b89a2511462f5f1c044fbaa9fff0235309877  THREAT_MODEL.md
230a613cea5dbe1cfd8532290103dcc5d70342c0ae74d350ab57fdf3f5d77632  BASELINE.md
c3dc51a6c978753fbe490f80eca469e74295535eef2e9ccc26b6718033f5135e  baseline_evidence_001.jsonl
b79d8832a9587482d7b00e41f716afd8444414f451c6cf2ca8179ed60714107b  baseline_appraisal_001.json
d2afaa45482b7ee03b6a96068d03cefd8d0b919df3a5afb109b43189d977ac13  NEWS_CONTEXT.md
```
