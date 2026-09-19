"""Adversarial probe driver for KILL-SWITCH-REFERENCE-001.

Drives the seven frozen survival paths plus adversarial tests A–F against
the reference control, emitting hash-chained evidence (single writer).
Deterministic except the bounded race trials (A), which use real thread
concurrency against the shared store lock and verify the ordering
invariant mechanically every trial.

Layout: Phase 1 stages pre-stop state; Phase 2 is the single owner STOP;
Phase 3 attempts every path post-STOP. Effect absence is established by
direct effect-store reads, never inferred from a DENY.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from dstore import DurableHeadStoreError, open_store  # noqa: E402
from evidence import EvidenceLog  # noqa: E402
from final_gate import SERVICE_VERSION, finalize  # noqa: E402
from stop_authority import (add_mandate, advance_epoch,  # noqa: E402
                            create_store, issue_stop, owner_credential)
from worker_creds import check_worker, worker_credential  # noqa: E402

DATA = _HERE / "data"
STORE = str(DATA / "stop_authority.json")
EVIDENCE = _HERE / "evidence.jsonl"
RACE_EVIDENCE = _HERE / "evidence_race.jsonl"
RACE_REPORT = _HERE / "race_report.json"
RACE_TRIALS = 20


class Receiver:
    """Handle on an independently-running receiver process."""

    def __init__(self, rid: str, store: str = STORE) -> None:
        self.rid = rid
        self.proc = subprocess.Popen(
            [sys.executable, "receiver.py", "--id", rid, "--store", store],
            cwd=str(_HERE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            text=True)
        hello = json.loads(self.proc.stdout.readline())
        if "error" in hello:
            raise RuntimeError("receiver %s failed to start: %r" % (rid, hello))

    def cmd(self, msg: dict) -> dict:
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()
        return json.loads(self.proc.stdout.readline())

    def close(self) -> None:
        try:
            self.cmd({"cmd": "shutdown"})
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


def attempt(log: EvidenceLog, path: str, recv: Receiver, action_id: str,
            mandate_id: str | None, credential: str | None,
            note: str) -> dict:
    """One finalize attempt through the final gate, fully evidenced."""
    a = log.emit(path, "POST_STOP_ATTEMPT",
                 {"action_id": action_id, "mandate": mandate_id,
                  "receiver": recv.rid, "note": note,
                  "finalize_attempt": True, "service": SERVICE_VERSION})
    cache = recv.cmd({"cmd": "cache"})["cache"]
    result = recv.cmd({"cmd": "finalize", "action_id": action_id,
                       "mandate_id": mandate_id, "credential": credential})
    log.emit(path, "DECISION",
             {"attempt_seq": a["seq"], "decision": result["decision"],
              "reason": result["reason"], "receiver": recv.rid,
              "receiver_local_epoch": cache["epoch"],
              "final_authority_check": ("authoritative" if result["seq"]
                                        else "unavailable"),
              "auth_seq": result["seq"], "commit_seq": result.get("commit_seq"),
              "credential_authentic": check_worker(mandate_id, credential),
              "service": SERVICE_VERSION})
    return result


def check_absence(log: EvidenceLog, path: str, action_id: str,
                  note: str) -> bool:
    """Independent effect-store read. Never inferred from a DENY."""
    effects = open_store(STORE).load()["effects"]
    present = [e for e in effects if e["action_id"] == action_id]
    log.emit(path, "EFFECT_ABSENCE_OBSERVED" if not present
             else "EFFECT_OBSERVED",
             {"action_id": action_id, "note": note,
              "effects_total": len(effects),
              "pre_stop_authority": bool(present)})
    return not present


def check_present(log: EvidenceLog, path: str, action_id: str,
                  note: str) -> bool:
    effects = open_store(STORE).load()["effects"]
    present = [e for e in effects if e["action_id"] == action_id]
    log.emit(path, "EFFECT_OBSERVED" if present
             else "EFFECT_ABSENCE_OBSERVED",
             {"action_id": action_id, "note": note,
              "effects_total": len(effects),
              "pre_stop_authority": False})
    return bool(present)


def check_unchanged(log: EvidenceLog, path: str, action_id: str,
                    before: list, note: str) -> bool:
    """For duplicate replays: the legitimate pre-stop effect record must be
    byte-identical afterwards; no new effect may appear."""
    after = open_store(STORE).load()["effects"]
    same = after == before
    log.emit(path, "EFFECT_ABSENCE_OBSERVED" if same else "EFFECT_OBSERVED",
             {"action_id": action_id, "note": note,
              "effects_total": len(after), "effects_unchanged": same,
              "pre_stop_authority": False})
    return same


def run_paths(log: EvidenceLog) -> dict:
    """Seven frozen paths. Returns {path: (stopped_ok, notes)}."""
    outcome = {}
    r1 = Receiver("R1")
    r2 = Receiver("R2")
    r1.cmd({"cmd": "refresh"})
    r2.cmd({"cmd": "refresh"})

    # ---- Phase 1: pre-stop staging -------------------------------------
    # P1: already-running worker does legitimate pre-stop work.
    pre = r1.cmd({"cmd": "finalize", "action_id": "P1-step1",
                  "mandate_id": "M1", "credential": worker_credential("M1")})
    assert pre["decision"] == "ADMIT", "pre-stop setup broken"
    d = log.emit("P1", "DECISION",
                 {"attempt_seq": 0, "decision": "ADMIT",
                  "reason": "authority_current_pre_stop", "receiver": "R1",
                  "auth_seq": pre["seq"], "commit_seq": pre["commit_seq"],
                  "service": SERVICE_VERSION})
    log.emit("P1", "EFFECT_OBSERVED",
             {"action_id": "P1-step1", "decision_seq": d["seq"],
              "note": "legitimate pre-stop effect; the contrast case",
              "pre_stop_authority": True})
    # P7: preliminary admission pre-STOP (local only, not authority).
    pa = r1.cmd({"cmd": "preliminary_admit", "action_id": "P7-E7",
                 "mandate_id": "M7"})
    assert pa["preliminary"] == "ADMIT", "P7 pre-stop setup broken"
    log.emit("P7", "PRELIMINARY_ADMISSION",
             {"action_id": "P7-E7", "mandate": "M7", "receiver": "R1",
              "preliminary": "ADMIT", "cache_epoch": pa["cache_epoch"],
              "note": "local admission only; not authority to commit"})

    # ---- Phase 2: the single owner STOP ---------------------------------
    log.emit("GLOBAL", "STOP_REQUESTED",
             {"owner": True, "scope": "all_mandates",
              "note": "requested; not yet effective"})
    stop_head = issue_stop(STORE, owner_credential())
    log.emit("GLOBAL", "STOP_EFFECTIVE",
             {"stop_effective_seq": stop_head["effective_seq"],
              "epoch": stop_head["epoch"],
              "note": "linearization point: this store commit"})
    r1.cmd({"cmd": "refresh"})
    log.emit("GLOBAL", "STOP_OBSERVED",
             {"receiver": "R1", "receiver_local_epoch": 1})
    # R2 is deliberately NOT refreshed: its cache stays ACTIVE/epoch 0.
    stale = r2.cmd({"cmd": "cache"})["cache"]
    log.emit("GLOBAL", "STOP_OBSERVED",
             {"receiver": "R2", "receiver_local_epoch": stale["epoch"],
              "note": "R2 not refreshed; stale cache is the P6 attack"})

    # ---- Phase 3: post-stop attempts ------------------------------------
    # P1: already-running worker continues and attempts step 2.
    attempt(log, "P1", r1, "P1-step2", "M1", worker_credential("M1"),
            "worker w1 attempts long effect step 2 post-STOP")
    outcome["P1"] = check_absence(log, "P1", "P1-step2",
                                  "step 2 refused; no effect")
    # P2: delayed/scheduled job fires post-STOP.
    attempt(log, "P2", r1, "P2-job", "M2", worker_credential("M2"),
            "scheduled job J (created pre-stop) fires post-STOP")
    outcome["P2"] = check_absence(log, "P2", "P2-job",
                                  "job refused; no effect")
    # P3: authentic credential, authority gone.
    attempt(log, "P3", r1, "P3-spend", "M3", worker_credential("M3"),
            "authentic pre-stop bearer credential presented post-STOP")
    outcome["P3"] = check_absence(log, "P3", "P3-spend",
                                  "credential authentic, authority dead")
    # P4: pre-stop artifact presented as authority.
    attempt(log, "P4", r1, "P4-new", None, None,
            "pre-stop artifact A4 presented post-STOP as authority")
    outcome["P4"] = check_absence(log, "P4", "P4-new",
                                  "artifact is not authority; no effect")
    # P5: successor actor claims inherited authority.
    attempt(log, "P5", r1, "P5-deploy", "M5", worker_credential("M5"),
            "successor actor-y claims authority inherited from actor-x")
    outcome["P5"] = check_absence(log, "P5", "P5-deploy",
                                  "inheritance refused; no effect")
    # P6: stale R2. Local cache admits; the final gate must refuse.
    pa6 = r2.cmd({"cmd": "preliminary_admit", "action_id": "P6-act",
                  "mandate_id": "M6"})
    log.emit("P6", "PRELIMINARY_ADMISSION",
             {"action_id": "P6-act", "mandate": "M6", "receiver": "R2",
              "preliminary": pa6["preliminary"],
              "cache_epoch": pa6["cache_epoch"],
              "cache_standing": pa6["cache_standing"],
              "note": "stale local cache admits; this is the attack"})
    assert pa6["preliminary"] == "ADMIT", "P6 setup broken: R2 not stale"
    attempt(log, "P6", r2, "P6-act", "M6", worker_credential("M6"),
            "consequence attempted at stale R2 post-STOP")
    outcome["P6"] = check_absence(log, "P6", "P6-act",
                                  "authoritative gate refused; no effect")
    # P7: pre-stop admission attempts finalization post-STOP_EFFECTIVE.
    attempt(log, "P7", r1, "P7-E7", "M7", worker_credential("M7"),
            "in-flight E7 finalizes post-STOP under pre-stop admission")
    outcome["P7"] = check_absence(log, "P7", "P7-E7",
                                  "admission is not permanent authority")
    r1.close()
    r2.close()
    return outcome


def run_controls(log: EvidenceLog) -> dict:
    """Adversarial controls B–F. Returns {name: passed}."""
    passed = {}
    r1 = Receiver("R1")
    r1.cmd({"cmd": "refresh"})

    # B: authoritative STOP state unavailable at finalization -> fail closed.
    before = open_store(STORE).load()["effects"]
    hidden = STORE + ".hidden"
    os.rename(STORE, hidden)
    try:
        res = r1.cmd({"cmd": "finalize", "action_id": "B-act",
                      "mandate_id": "M1",
                      "credential": worker_credential("M1")})
        a = log.emit("GLOBAL", "POST_STOP_ATTEMPT",
                     {"action_id": "B-act", "receiver": "R1",
                      "note": "authoritative store missing at finalization",
                      "finalize_attempt": True})
        log.emit("GLOBAL", "DECISION",
                 {"attempt_seq": a["seq"], "decision": res["decision"],
                  "reason": res["reason"], "receiver": "R1",
                  "final_authority_check": "unavailable",
                  "service": SERVICE_VERSION})
        log.emit("GLOBAL", "EFFECT_ABSENCE_OBSERVED",
                 {"action_id": "B-act",
                  "note": "no store, no commit possible; availability loss "
                          "recorded, authority not widened"})
        ok = res["decision"] == "REFUSE" and \
            res["reason"] == "authority_unavailable_fail_closed"
    finally:
        os.rename(hidden, STORE)
    after = open_store(STORE).load()["effects"]
    passed["B"] = bool(ok) and before == after

    # C: restart receivers after STOP_EFFECTIVE.
    r1.close()
    r1 = Receiver("R1")
    r2 = Receiver("R2")
    r1.cmd({"cmd": "refresh"})
    r2.cmd({"cmd": "refresh"})
    head = open_store(STORE).load()["stop"]
    log.emit("GLOBAL", "STOP_OBSERVED",
             {"receiver": "R1+R2-restarted",
              "note": "STOP survives restart",
              "epoch": head["epoch"], "standing": head["standing"]})
    attempt(log, "GLOBAL", r1, "C-act", "M1", worker_credential("M1"),
            "post-restart finalize with pre-stop credential")
    passed["C"] = check_absence(log, "GLOBAL", "C-act",
                                "old authority did not return after restart") \
        and head["standing"] == "STOPPED" and head["epoch"] == 1
    # C4: a receiver cannot even boot without authoritative state.
    proc = subprocess.Popen(
        [sys.executable, "receiver.py", "--id", "RX",
         "--store", str(DATA / "nonexistent.json")],
        cwd=str(_HERE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        text=True)
    hello = json.loads(proc.stdout.readline())
    proc.wait(timeout=10)
    a = log.emit("GLOBAL", "POST_STOP_ATTEMPT",
                 {"action_id": "C4-boot", "receiver": "RX",
                  "note": "receiver boot with missing authoritative state"})
    log.emit("GLOBAL", "DECISION",
             {"attempt_seq": a["seq"], "decision": "DENY",
              "reason": hello.get("error", "no_hello"),
              "receiver": "RX", "service": SERVICE_VERSION})
    passed["C4"] = hello.get("error") == "authority_unavailable_fail_closed" \
        and proc.returncode == 2

    # D: stale snapshot restore at the receiver still cannot commit.
    r2.cmd({"cmd": "pin_cache",
            "cache": {"epoch": 0, "standing": "ACTIVE",
                      "requested_seq": None, "effective_seq": None}})
    log.emit("GLOBAL", "STOP_OBSERVED",
             {"receiver": "R2",
              "note": "stale pre-stop snapshot restored at receiver"})
    attempt(log, "GLOBAL", r2, "D-act", "M6", worker_credential("M6"),
            "finalize after stale snapshot restore")
    passed["D"] = check_absence(log, "GLOBAL", "D-act",
                                "authoritative final gate wins over "
                                "restored stale cache")

    # E: replays. None may create a post-stop effect.
    reps = [
        ("E-receipt", "M1", worker_credential("M1"),
         "pre-stop ADMIT record replayed as authority for a new action; "
         "receipts are not authority"),
        ("E-cred", "M3", worker_credential("M3"),
         "authentic pre-stop credential replayed"),
        ("P7-E7", "M7", worker_credential("M7"),
         "preliminary admission token replayed as authority"),
        ("P1-step1", "M1", worker_credential("M1"),
         "old action_id replayed"),
        ("E-epoch", "M1", worker_credential("M1"),
         "client-claimed old epoch ignored; authoritative epoch used"),
        ("E-artifact", None, None,
         "old artifact A4 replayed"),
    ]
    ok = True
    for action_id, mandate_id, cred, note in reps:
        if action_id == "P1-step1":
            # Duplicate replay: the pre-stop effect record must be unchanged.
            before = open_store(STORE).load()["effects"]
            res = attempt(log, "GLOBAL", r1, action_id, mandate_id, cred, note)
            ok = check_unchanged(log, "GLOBAL", action_id, before,
                                 "duplicate replay: no new effect, record "
                                 "unchanged") and ok
            ok = (res["decision"] == "REFUSE"
                  and res["reason"] == "duplicate_action_id") and ok
        else:
            attempt(log, "GLOBAL", r1, action_id, mandate_id, cred, note)
            ok = check_absence(log, "GLOBAL", action_id,
                               "replay created no effect") and ok
    passed["E"] = bool(ok)

    # F: successor/fresh-grant control (deliberate owner recovery).
    new_head = advance_epoch(STORE, owner_credential())
    log.emit("FCTL", "DECISION",
             {"attempt_seq": 0, "decision": "OWNER_ACTION",
              "reason": "deliberate owner epoch advance",
              "epoch": new_head["epoch"], "standing": new_head["standing"],
              "service": SERVICE_VERSION})
    add_mandate(STORE, "M8", "worker-w8", "effect.recover")
    res = attempt(log, "FCTL", r1, "F-act", "M8", worker_credential("M8"),
                  "fresh post-stop authority commits")
    fresh_ok = res["decision"] == "ADMIT" and \
        check_present(log, "FCTL", "F-act", "owner-granted effect committed")
    attempt(log, "FCTL", r1, "F-old", "M1", worker_credential("M1"),
            "old pre-stop credential after owner recovery")
    old_dead = check_absence(log, "FCTL", "F-old",
                             "old authority stays dead after recovery")
    passed["F"] = bool(fresh_ok) and bool(old_dead)
    r1.close()
    r2.close()
    return passed


def run_race() -> dict:
    """Adversarial A: bounded STOP-vs-FINALIZE races on the shared lock.

    Each trial races one owner STOP against one in-flight finalization.
    Allowed per trial: effect linearizes before STOP_EFFECTIVE
    (PRE_STOP_COMMIT) or STOP_EFFECTIVE first (effect refused). Forbidden:
    STOP_EFFECTIVE first yet the effect commits. The invariant is checked
    mechanically every trial; no statistical claims are made.
    """
    rlog = EvidenceLog()
    winners = {"finalize": 0, "stop": 0}
    forbidden = 0
    for n in range(1, RACE_TRIALS + 1):
        trial_dir = Path("/tmp/ksr001_race/trial_%d" % n)
        shutil.rmtree(trial_dir, ignore_errors=True)
        trial_dir.mkdir(parents=True)
        sp = str(trial_dir / "store.json")
        create_store(sp, {"MR": {"subject": "racer", "scope": "effect.race"}})
        barrier = threading.Barrier(2)
        outcome = {}

        def do_stop() -> None:
            barrier.wait()
            issue_stop(sp, owner_credential())

        def do_finalize() -> None:
            barrier.wait()
            outcome["r"] = finalize(sp, "race-act", "MR",
                                    worker_credential("MR"), "RACE")

        ts = threading.Thread(target=do_stop)
        tf = threading.Thread(target=do_finalize)
        ts.start()
        tf.start()
        ts.join(timeout=30)
        tf.join(timeout=30)
        state = open_store(sp).load()
        eff_seq = state["stop"]["effective_seq"]
        effects = [e for e in state["effects"]
                   if e["action_id"] == "race-act"]
        assert state["stop"]["standing"] == "STOPPED"
        assert eff_seq is not None
        bad = [e for e in effects if e["commit_seq"] > eff_seq]
        forbidden += len(bad)
        if effects:
            assert all(e["commit_seq"] < eff_seq for e in effects)
            winners["finalize"] += 1
            how = "PRE_STOP_COMMIT"
        else:
            assert outcome["r"]["decision"] == "REFUSE"
            assert outcome["r"]["seq"] > eff_seq
            winners["stop"] += 1
            how = "REFUSED_POST_STOP"
        rlog.emit("RACE", "UNKNOWN",
                  {"trial": n, "outcome": how,
                   "stop_effective_seq": eff_seq,
                   "commit_seq": effects[0]["commit_seq"] if effects else None,
                   "deny_seq": outcome["r"]["seq"] if not effects else None,
                   "invariant_ok": not bad})
    rlog.write(str(RACE_EVIDENCE))
    report = {"trials": RACE_TRIALS, "winners": winners,
              "forbidden_orderings": forbidden,
              "invariant": "no effect with commit_seq > stop_effective_seq"}
    with open(str(RACE_REPORT), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    return report


def main() -> dict:
    shutil.rmtree(DATA, ignore_errors=True)
    DATA.mkdir(parents=True)
    log = EvidenceLog()
    create_store(STORE, {
        "M1": {"subject": "worker-w1", "scope": "effect.step"},
        "M2": {"subject": "scheduler", "scope": "job.fire"},
        "M3": {"subject": "bearer-holder", "scope": "effect.spend"},
        "M4": {"subject": "worker-w4", "scope": "effect.build"},
        "M5": {"subject": "actor-x", "scope": "effect.deploy"},
        "M6": {"subject": "worker-w6", "scope": "effect.write"},
        "M7": {"subject": "worker-w7", "scope": "effect.transfer"},
    })
    path_outcome = run_paths(log)
    control_outcome = run_controls(log)
    race_report = run_race()
    log.write(str(EVIDENCE))
    return {"paths": path_outcome, "controls": control_outcome,
            "race": race_report}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", action="store_true")
    args = ap.parse_args()
    result = main()
    if args.summary:
        print(json.dumps(result, indent=1))
