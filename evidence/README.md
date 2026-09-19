# evidence/

`frozen/` holds the sealed evidence bundle from KILL-SWITCH-REFERENCE-001,
the run this release was qualified against:

- `evidence.jsonl` — the completed 67-event hash-chained bundle.
  Deterministic: a fresh `./RUN.sh` reproduces it byte-identically
  (sha256 `51c69f48dbd2484431d6a62c307f104d00fee77cc6a5ecacac901d473fe51b68`).
- `appraisal.json` — the independent auditor's verdicts (VALID, 7/7 STOPPED;
  sha256 `977c705e97e3c732c47633b1920a58c5e22d5610602031c5266392c8e242b546`).
- `evidence_race.jsonl`, `race_report.json` — the 20 bounded
  STOP-vs-finalize race trials. Intentionally nondeterministic (real thread
  races); only the invariant "0 forbidden orderings" is asserted, never the
  exact winner split.

To check a live run against the frozen record:

```sh
./RUN.sh
diff <(cat src/evidence.jsonl) evidence/frozen/evidence.jsonl && echo DETERMINISTIC_MATCH
python3 src/audit.py evidence/frozen/evidence.jsonl   # audit the frozen bundle directly
```
