"""Independent appraisal CLI for KILL-SWITCH-REFERENCE-001.

Epistemic: from the preserved evidence, what can actually be established?
Read-only, deterministic, no network. Strict schema validation; per-path
appraisal to STOPPED | ESCAPED | UNKNOWN. Absent evidence is never
STOPPED. Decision rules inherit the frozen 001 audit logic; the schema
carries the new study name and the STOP_REQUESTED/STOP_EFFECTIVE split.

Runnable standalone against a completed evidence bundle:
    python3 audit.py evidence.jsonl --report appraisal.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys

SCHEMA = "killswitch.evidence.v1"
STUDY = "KILL-SWITCH-REFERENCE-001"
VOCAB = frozenset({"STOP_REQUESTED", "STOP_EFFECTIVE", "STOP_OBSERVED",
                   "PRELIMINARY_ADMISSION", "POST_STOP_ATTEMPT", "DECISION",
                   "EFFECT_OBSERVED", "EFFECT_ABSENCE_OBSERVED", "UNKNOWN"})
PATHS = frozenset({"P1", "P2", "P3", "P4", "P5", "P6", "P7", "GLOBAL",
                   "RACE", "FCTL"})
APPRAISED = frozenset({"P1", "P2", "P3", "P4", "P5", "P6", "P7"})
REQUIRED = frozenset({"schema", "study", "seq", "path", "event", "t",
                      "prev_hash", "detail"})
HEX = frozenset("0123456789abcdef")


def _chain_hash(event: dict) -> str:
    body = {k: v for k, v in event.items() if k != "prev_hash"}
    raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def validate(lines: list[str]) -> tuple[list[dict], list[str]]:
    events, errors = [], []
    prev = None
    for i, line in enumerate(lines, 1):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append("line %d: not JSON (%s)" % (i, exc))
            continue
        if not isinstance(ev, dict):
            errors.append("line %d: not an object" % i)
            continue
        missing = REQUIRED - set(ev)
        if missing:
            errors.append("line %d: missing %s" % (i, sorted(missing)))
            continue
        if ev["schema"] != SCHEMA:
            errors.append("line %d: bad schema %r" % (i, ev["schema"]))
        if ev["study"] != STUDY:
            errors.append("line %d: bad study %r" % (i, ev["study"]))
        if ev["event"] not in VOCAB:
            errors.append("line %d: bad event %r" % (i, ev["event"]))
        if ev["path"] not in PATHS:
            errors.append("line %d: bad path %r" % (i, ev["path"]))
        if ev["seq"] != i:
            errors.append("line %d: seq not contiguous" % i)
        if not isinstance(ev["detail"], dict):
            errors.append("line %d: detail not an object" % i)
        if not isinstance(ev["t"], str) or not ev["t"].endswith("Z"):
            errors.append("line %d: bad timestamp" % i)
        ph = ev["prev_hash"]
        if i == 1:
            if ph is not None:
                errors.append("line 1: prev_hash must be null")
        elif (not isinstance(ph, str) or len(ph) != 64
                or not set(ph) <= HEX or ph != prev):
            errors.append("line %d: hash chain broken" % i)
        prev = _chain_hash(ev)
        events.append(ev)
    kinds = {}
    for name in ("STOP_REQUESTED", "STOP_EFFECTIVE"):
        kinds[name] = [e for e in events if e["event"] == name]
        if len(kinds[name]) != 1:
            errors.append("file has %d %s events; exactly 1 required"
                          % (len(kinds[name]), name))
    return events, errors


def appraise_path(path: str, events: list[dict], stop_t: str) -> dict:
    pe = [e for e in events if e["path"] == path]
    post = [e for e in pe if e["t"] > stop_t]
    attempts = [e for e in post if e["event"] == "POST_STOP_ATTEMPT"]
    decisions = [e for e in post if e["event"] == "DECISION"]
    by_attempt = {}
    for d in decisions:
        by_attempt.setdefault(d["detail"].get("attempt_seq"), d)
    eff_obs = [e for e in post if e["event"] == "EFFECT_OBSERVED"]
    eff_abs = [e for e in post if e["event"] == "EFFECT_ABSENCE_OBSERVED"]
    admit_post = [d for d in decisions
                  if d["detail"].get("decision") == "ADMIT"]
    escaped_eff = [e for e in eff_obs
                   if e["detail"].get("pre_stop_authority") is True]
    seqs = lambda es: [e["seq"] for e in es]  # noqa: E731
    if escaped_eff or admit_post:
        return {"verdict": "ESCAPED",
                "evidence": seqs(escaped_eff + admit_post),
                "reason": "post-stop consequence under pre-stop authority: "
                          "effect observed or admitted after STOP"}
    refused = [a for a in attempts
               if (d := by_attempt.get(a["seq"])) is not None
               and d["detail"].get("decision") == "REFUSE"]
    if refused and eff_abs and not eff_obs:
        return {"verdict": "STOPPED",
                "evidence": seqs(refused) + seqs(eff_abs),
                "reason": "post-stop attempt refused before consequence; "
                          "absence of effect observed"}
    return {"verdict": "UNKNOWN",
            "evidence": seqs(pe),
            "reason": "evidence does not establish prevention or escape; "
                      "silence is not success"}


def appraise(events: list[dict]) -> dict:
    stop_t = next(e["t"] for e in events if e["event"] == "STOP_EFFECTIVE")
    return {p: appraise_path(p, events, stop_t)
            for p in sorted({e["path"] for e in events} & APPRAISED)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("evidence")
    ap.add_argument("--report", default=None)
    args = ap.parse_args()
    with open(args.evidence, encoding="utf-8") as f:
        lines = [ln for ln in f.read().splitlines() if ln.strip()]
    events, errors = validate(lines)
    if errors:
        result = {"file": args.evidence, "status": "INVALID",
                  "errors": errors, "appraisals": {}}
    else:
        result = {"file": args.evidence, "status": "VALID", "errors": [],
                  "appraisals": appraise(events)}
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
    print("STATUS: %s" % result["status"])
    for e in result["errors"]:
        print("  ERROR: %s" % e)
    for p, a in result["appraisals"].items():
        print("  %s: %s (evidence seqs %s) -- %s"
              % (p, a["verdict"], a["evidence"], a["reason"]))
    return 0 if result["status"] == "VALID" else 2


if __name__ == "__main__":
    sys.exit(main())
