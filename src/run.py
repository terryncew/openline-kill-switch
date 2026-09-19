"""One-command runner for KILL-SWITCH-REFERENCE-001.

Runs the probe suite exactly once (seven paths + adversarial controls
A-F), then runs the independent auditor against the completed evidence
bundle.

    python3 run.py

Artifacts: evidence.jsonl, evidence_race.jsonl, race_report.json,
appraisal.json, data/stop_authority.json
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def main() -> int:
    r = subprocess.run([sys.executable, "probes.py", "--summary"],
                       cwd=str(_HERE), capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        return r.returncode
    summary = json.loads(r.stdout)
    r = subprocess.run(
        [sys.executable, "audit.py", "evidence.jsonl",
         "--report", "appraisal.json"],
        cwd=str(_HERE), capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        return r.returncode
    with open(_HERE / "appraisal.json", encoding="utf-8") as f:
        appraisal = json.load(f)
    verdicts = {p: a["verdict"]
                for p, a in appraisal["appraisals"].items()}
    paths_ok = (sorted(verdicts) == ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]
                and all(v == "STOPPED" for v in verdicts.values()))
    controls_ok = all(summary["controls"].values())
    race_ok = summary["race"]["forbidden_orderings"] == 0
    print("PATHS_7/7_STOPPED:", paths_ok, verdicts)
    print("CONTROLS_B-F:", controls_ok, summary["controls"])
    print("RACE_FORBIDDEN:", summary["race"]["forbidden_orderings"],
          "winners:", summary["race"]["winners"])
    return 0 if (appraisal["status"] == "VALID" and paths_ok
                 and controls_ok and race_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
