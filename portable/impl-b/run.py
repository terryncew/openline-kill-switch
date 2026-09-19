"""Run harness for KILL-SWITCH-PORTABILITY-001, Implementation B.

Executes the seven frozen paths P1-P7 plus controls B-F against the
SQLite-transaction gate, then the 20-race STOP-vs-finalize protocol.
Writes hash-chained evidence (contract section 5 vocabulary) to
evidence/evidence.jsonl (deterministic across runs) and
evidence/race_evidence.jsonl (20 race trials; winners nondeterministic,
invariant asserted).

Stdlib only. No network. No secrets beyond study-local stand-ins.
"""

import os
import shutil
import sqlite3
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from killswitch_b.evidence import EvidenceLog
from killswitch_b.roles import Owner, Receiver, Worker, open_db

BASE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(BASE, "work")
EVDIR = os.path.join(BASE, "evidence")


# ---- evidence helpers ----------------------------------------------------
def ev_stop_issued(ev, label, stop_result):
    ev.append("STOP_ISSUED", label, {
        "new_epoch": stop_result["new_epoch"],
        "stop_journal_rowid": stop_result["stop_journal_rowid"],
        "note": "owner invoked STOP; propagation not assumed",
    })


def ev_stop_observed(ev, label, db, observed_by):
    st = db.read_stop()
    ev.append("STOP_OBSERVED", label, {
        "stop_journal_rowid": st["stop_rowid"],
        "authoritative_epoch": st["epoch"],
        "observed_by": observed_by,
        "note": "STOP_EFFECTIVE reached the serialization boundary",
    })
    return st["stop_rowid"]


def ev_attempt(ev, label, action_id, actor, authority_presented, stop_rowid,
               extra=None):
    payload = {"action_id": action_id, "actor": actor,
               "authority_presented": authority_presented,
               "stop_journal_rowid": stop_rowid,
               "note": "covered effect attempted after STOP"}
    if extra:
        payload.update(extra)
    ev.append("POST_STOP_ATTEMPT", label, payload)


def ev_decision(ev, label, res, store="authoritative", extra=None):
    payload = {"decision": res["decision"], "reason": res["reason"],
               "action_id": res["action_id"], "actor": res["actor"],
               "attempt_journal_rowid": res["journal_rowid"],
               "stop_journal_rowid": res["stop_rowid"],
               "authoritative_epoch": res["epoch"], "store": store}
    if res.get("grant_id") is not None:
        payload["grant_id"] = res["grant_id"]
    if res.get("mac_valid") is not None:
        payload["mac_valid"] = res["mac_valid"]
    if extra:
        payload.update(extra)
    ev.append("DECISION", label, payload)


def ev_effect_check(ev, label, db, action_id, store="authoritative"):
    if db.effect_present(action_id):
        ev.append("EFFECT_OBSERVED", label, {
            "action_id": action_id, "store": store,
            "effect_journal_rowid": db.effect_journal_rowid(action_id),
            "note": "effect present in the independent effect store"})
        return True
    ev.append("EFFECT_ABSENCE_OBSERVED", label, {
        "action_id": action_id, "store": store, "present": False,
        "note": "effect store checked directly; effect absent"})
    return False


def fresh_db(name):
    path = os.path.join(WORK, name + ".db")
    for suffix in ("", "-wal", "-shm", "-journal"):
        p = path + suffix if suffix else path
        if os.path.exists(p):
            os.remove(p)
    secret = "owner-secret-" + name
    db = open_db(path, secret)
    return db, secret, path


# ---- the seven paths -----------------------------------------------------
def path_p1(ev):
    """P1 already-running worker: honest pre-STOP commit, then STOP, then the
    worker keeps computing and attempts a protected consequence."""
    db, secret, _ = fresh_db("p1")
    owner, worker = Owner(db, secret), Worker("worker-1", db)
    r1 = worker.attempt("p1-pre")
    ev.append("DECISION", "P1", {
        "decision": r1["decision"], "reason": r1["reason"],
        "action_id": "p1-pre", "actor": "worker-1",
        "attempt_journal_rowid": r1["journal_rowid"],
        "stop_journal_rowid": None, "authoritative_epoch": 0,
        "store": "authoritative",
        "note": "honest pre-STOP commit; irreversible effects cannot be undone"})
    ev_effect_check(ev, "P1", db, "p1-pre")
    s = owner.issue_stop()
    ev_stop_issued(ev, "P1", s)
    stop_rowid = ev_stop_observed(ev, "P1", db, "harness")
    ev_attempt(ev, "P1", "p1-post", "worker-1", "none (kept computing)",
               stop_rowid)
    r2 = worker.attempt("p1-post")
    ev_decision(ev, "P1", r2)
    ev_effect_check(ev, "P1", db, "p1-post")
    db.close()


def path_p2(ev):
    """P2 delayed/scheduled job: created pre-STOP, executes post-STOP."""
    db, secret, _ = fresh_db("p2")
    owner, recv = Owner(db, secret), Receiver("receiver-1", db)
    ticket = recv.preliminary("p2-job")  # scheduled pre-STOP
    assert ticket["authoritative"] is False
    s = owner.issue_stop()
    ev_stop_issued(ev, "P2", s)
    stop_rowid = ev_stop_observed(ev, "P2", db, "harness")
    ev_attempt(ev, "P2", "p2-job", "scheduler",
               "pre-STOP scheduled job ticket (non-authoritative)",
               stop_rowid)
    r = recv.finalize("p2-job")
    ev_decision(ev, "P2", r)
    ev_effect_check(ev, "P2", db, "p2-job")
    db.close()


def path_p3(ev):
    """P3 outstanding credential: cryptographically authentic pre-STOP grant
    used after STOP. Authenticity is irrelevant; authority is gone."""
    db, secret, _ = fresh_db("p3")
    owner, worker = Owner(db, secret), Worker("worker-3", db)
    grant = owner.create_grant("cred-p3")
    s = owner.issue_stop()
    ev_stop_issued(ev, "P3", s)
    stop_rowid = ev_stop_observed(ev, "P3", db, "harness")
    ev_attempt(ev, "P3", "p3-use", "worker-3",
               "grant cred-p3 + MAC (authentic, pre-STOP)", stop_rowid)
    r = worker.attempt("p3-use", grant_id="cred-p3", grant_mac=grant["mac"])
    ev_decision(ev, "P3", r)
    ev_effect_check(ev, "P3", db, "p3-use")
    db.close()


def path_p4(ev):
    """P4 pre-stop artifact: preliminary-admission receipt presented as
    authority after STOP."""
    db, secret, _ = fresh_db("p4")
    owner, worker = Owner(db, secret), Worker("worker-4", db)
    artifact = worker._db.preliminary_admit("p4-artifact", "worker-4")
    s = owner.issue_stop()
    ev_stop_issued(ev, "P4", s)
    stop_rowid = ev_stop_observed(ev, "P4", db, "harness")
    ev_attempt(ev, "P4", "p4-use", "worker-4",
               "pre-STOP preliminary receipt rowid %d presented as authority"
               % artifact["preliminary_rowid"], stop_rowid)
    r = worker.attempt("p4-use")
    ev_decision(ev, "P4", r)
    ev_effect_check(ev, "P4", db, "p4-use")
    db.close()


def path_p5(ev):
    """P5 successor actor: different worker claims predecessor authority."""
    db, secret, _ = fresh_db("p5")
    owner = Owner(db, secret)
    pred = Worker("worker-5a", db)
    grant = owner.create_grant("cred-p5")
    r_pre = pred.attempt("p5-pre", grant_id="cred-p5", grant_mac=grant["mac"])
    assert r_pre["decision"] == "ADMIT"
    s = owner.issue_stop()
    ev_stop_issued(ev, "P5", s)
    stop_rowid = ev_stop_observed(ev, "P5", db, "harness")
    succ = Worker("worker-5b", db)  # successor, new actor
    ev_attempt(ev, "P5", "p5-succ", "worker-5b",
               "predecessor grant cred-p5 claimed as inherited authority",
               stop_rowid, extra={"original_actor": "worker-5a"})
    r = succ.attempt("p5-succ", grant_id="cred-p5", grant_mac=grant["mac"])
    ev_decision(ev, "P5", r)
    ev_effect_check(ev, "P5", db, "p5-succ")
    db.close()


def path_p6(ev):
    """P6 stale second receiver: R2's local epoch cache still says ACTIVE
    after STOP. R2 is NOT fixed by faster notification; the authoritative
    final gate must refuse."""
    db, secret, _ = fresh_db("p6")
    owner = Owner(db, secret)
    r2 = Receiver("R2", db)
    r2.sync()  # local cache = 0 (ACTIVE), pre-STOP
    r2.preliminary("p6-work")
    s = owner.issue_stop()
    ev_stop_issued(ev, "P6", s)
    stop_rowid = ev_stop_observed(ev, "P6", db, "harness")
    assert r2.local_epoch == 0, "R2 cache must be genuinely stale"
    ev_attempt(ev, "P6", "p6-work", "R2",
               "receiver-local cache said ACTIVE (stale); no re-sync performed",
               stop_rowid,
               extra={"receiver_local_epoch": r2.local_epoch,
                      "note": "stale local state is the test; the final gate "
                              "reads authoritative state"})
    r = r2.finalize("p6-work")
    ev_decision(ev, "P6", r)
    ev_effect_check(ev, "P6", db, "p6-work")
    db.close()


def path_p7(ev):
    """P7 in-flight work: preliminary admission pre-STOP, work begins, final
    effect not yet irreversible, STOP intervenes, finalization post-STOP."""
    db, secret, _ = fresh_db("p7")
    owner, recv = Owner(db, secret), Receiver("receiver-7", db)
    ticket = recv.preliminary("p7-final")
    ev.append("DECISION", "P7", {
        "decision": "PRELIMINARY", "reason": "NON_AUTHORITATIVE",
        "action_id": "p7-final", "actor": "receiver-7",
        "attempt_journal_rowid": ticket["preliminary_rowid"],
        "stop_journal_rowid": None, "authoritative_epoch": 0,
        "store": "authoritative",
        "note": "pre-STOP preliminary admission; explicitly not authority"})
    s = owner.issue_stop()
    ev_stop_issued(ev, "P7", s)
    stop_rowid = ev_stop_observed(ev, "P7", db, "harness")
    ev_attempt(ev, "P7", "p7-final", "receiver-7",
               "pre-STOP preliminary ticket; finalization attempted post-STOP",
               stop_rowid)
    r = recv.finalize("p7-final")
    ev_decision(ev, "P7", r)
    ev_effect_check(ev, "P7", db, "p7-final")
    db.close()


# ---- controls B-F --------------------------------------------------------
def control_b(ev):
    """B: authority DB unavailable at finalization -> fail closed, no effect,
    availability loss recorded."""
    bad_path = os.path.join(WORK, "no-such-dir-b", "gate.db")
    ev.append("POST_STOP_ATTEMPT", "B", {
        "action_id": "b-attempt", "actor": "worker-b",
        "authority_presented": "none",
        "note": "authority store unavailable at finalization"})
    try:
        db = open_db(bad_path, "owner-secret-b")
        db.finalize("b-attempt", "worker-b")
        db.close()
        ev.append("DECISION", "B", {
            "decision": "ADMIT", "reason": "UNEXPECTED",
            "action_id": "b-attempt", "store": "authoritative",
            "note": "FAIL: gate ran despite unavailable authority"})
    except Exception as exc:
        ev.append("DECISION", "B", {
            "decision": "REFUSE", "reason": "AUTHORITY_UNAVAILABLE",
            "action_id": "b-attempt", "actor": "worker-b",
            "attempt_journal_rowid": None, "stop_journal_rowid": None,
            "authoritative_epoch": None, "store": "authoritative",
            "note": "no gate transaction could run (%s); no effect possible; "
                    "availability loss recorded" % type(exc).__name__})
        ev.append("UNKNOWN", "B", {
            "matter": "effect-store check",
            "reason": "authority store unavailable, so absence is established "
                      "by 'no commit path existed', not by a store read"})


def control_c(ev):
    """C: restart. STOP survives process/DB restart; old authority stays dead."""
    db, secret, path = fresh_db("c")
    owner, worker = Owner(db, secret), Worker("worker-c", db)
    grant = owner.create_grant("cred-c")
    s = owner.issue_stop()
    ev_stop_issued(ev, "C", s)
    ev_stop_observed(ev, "C", db, "harness")
    db.close()  # process/DB restart: all connections dropped
    db2 = open_db(path, secret)
    st = db2.read_stop()
    assert st["epoch"] == 1, "STOP must survive restart"
    worker2 = Worker("worker-c", db2)
    ev_attempt(ev, "C", "c-post-restart", "worker-c",
               "pre-STOP grant cred-c presented after restart",
               st["stop_rowid"], extra={"restarted": True})
    r = worker2.attempt("c-post-restart", grant_id="cred-c",
                        grant_mac=grant["mac"])
    ev_decision(ev, "C", r)
    ev_effect_check(ev, "C", db2, "c-post-restart")
    db2.close()


def control_d(ev):
    """D: stale snapshot restore cannot commit through the authoritative
    final gate. A commit into the stale copy is inert: absent from the
    authoritative effect store."""
    db, secret, path = fresh_db("d")
    owner = Owner(db, secret)
    owner.create_grant("cred-d")
    snap_path = os.path.join(WORK, "d-snapshot.db")
    if os.path.exists(snap_path):
        os.remove(snap_path)
    src = sqlite3.connect(path)
    dst = sqlite3.connect(snap_path)
    src.backup(dst)
    dst.close()
    src.close()
    s = owner.issue_stop()
    ev_stop_issued(ev, "D", s)
    stop_rowid = ev_stop_observed(ev, "D", db, "harness")
    r2 = Receiver("R2d", db)
    stale_epoch = r2.restore_stale_snapshot(open_db(snap_path, secret))
    assert stale_epoch == 0
    ev_attempt(ev, "D", "d-live", "R2d",
               "stale snapshot restored as receiver-local belief (epoch 0); "
               "finalize attempted through the authoritative gate",
               stop_rowid, extra={"receiver_local_epoch": stale_epoch})
    r = r2.finalize("d-live")
    ev_decision(ev, "D", r)
    ev_effect_check(ev, "D", db, "d-live")
    # The stale copy itself still admits (epoch 0 there) - but that commit is
    # inert: it never reaches the authoritative store.
    snap_db = open_db(snap_path, secret)
    rs = snap_db.finalize("d-snap", "R2d")
    ev.append("DECISION", "D", {
        "decision": rs["decision"], "reason": rs["reason"],
        "action_id": "d-snap", "actor": "R2d",
        "attempt_journal_rowid": rs["journal_rowid"],
        "stop_journal_rowid": None, "authoritative_epoch": 0,
        "store": "stale_snapshot_copy",
        "note": "commit into the stale copy only; not the authoritative gate"})
    ev_effect_check(ev, "D", snap_db, "d-snap", store="stale_snapshot_copy")
    ev_effect_check(ev, "D", db, "d-snap", store="authoritative")
    snap_db.close()
    db.close()


def control_e(ev):
    """E: replays of pre-stop tokens/action_ids/epochs create no post-stop
    effect."""
    db, secret, _ = fresh_db("e")
    owner, worker = Owner(db, secret), Worker("worker-e", db)
    grant = owner.create_grant("cred-e")
    r_pre = worker.attempt("e-pre", grant_id="cred-e", grant_mac=grant["mac"])
    assert r_pre["decision"] == "ADMIT"
    s = owner.issue_stop()
    ev_stop_issued(ev, "E", s)
    stop_rowid = ev_stop_observed(ev, "E", db, "harness")
    replays = [
        ("e-replay-grant", "pre-STOP grant cred-e re-presented",
         {"grant_id": "cred-e", "grant_mac": grant["mac"]}),
        ("e-pre", "pre-STOP action_id replayed (duplicate)", {}),
        ("e-replay-epoch", "stale epoch value presented as authority",
         {"grant_id": "epoch:0", "grant_mac": "bogus"}),
    ]
    for action_id, presented, kw in replays:
        ev_attempt(ev, "E", action_id, "worker-e", presented, stop_rowid)
        r = worker.attempt(action_id, **kw)
        ev_decision(ev, "E", r)
        ev_effect_check(ev, "E", db, action_id)
    db.close()


def control_f(ev):
    """F: owner-only fresh grant after STOP permits a new effect while old
    authority stays dead."""
    db, secret, _ = fresh_db("f")
    owner, worker = Owner(db, secret), Worker("worker-f", db)
    old_grant = owner.create_grant("cred-f-old")
    s = owner.issue_stop()
    ev_stop_issued(ev, "F", s)
    stop_rowid = ev_stop_observed(ev, "F", db, "harness")
    new_grant = owner.create_grant("cred-f-new")  # owner-only, post-STOP
    assert new_grant["issued_rowid"] > stop_rowid
    ev_attempt(ev, "F", "f-old", "worker-f",
               "pre-STOP grant cred-f-old re-presented", stop_rowid)
    r_old = worker.attempt("f-old", grant_id="cred-f-old",
                           grant_mac=old_grant["mac"])
    ev_decision(ev, "F", r_old)
    ev_effect_check(ev, "F", db, "f-old")
    ev_attempt(ev, "F", "f-new", "worker-f",
               "fresh post-STOP owner grant cred-f-new", stop_rowid,
               extra={"grant_issued_rowid": new_grant["issued_rowid"]})
    r_new = worker.attempt("f-new", grant_id="cred-f-new",
                           grant_mac=new_grant["mac"])
    ev_decision(ev, "F", r_new,
                extra={"grant_issued_rowid": new_grant["issued_rowid"]})
    ev_effect_check(ev, "F", db, "f-new")
    db.close()


# ---- 20-race protocol -----------------------------------------------------
def race_trial(i, ev):
    """One bounded STOP-vs-finalize race on a fresh DB. Forbidden ordering:
    STOP_EFFECTIVE-first yet the effect commits."""
    path = os.path.join(WORK, "race-%02d.db" % i)
    for suffix in ("", "-wal", "-shm"):
        p = path + suffix if suffix else path
        if os.path.exists(p):
            os.remove(p)
    secret = "owner-secret-race"
    setup = open_db(path, secret)
    owner = Owner(setup, secret)
    grant = owner.create_grant("race-grant")
    setup.close()

    barrier = threading.Barrier(2)
    out = {}

    def do_stop():
        db = open_db(path, secret)
        barrier.wait()
        try:
            out["stop"] = Owner(db, secret).issue_stop()
        finally:
            db.close()

    def do_finalize():
        db = open_db(path, secret)
        barrier.wait()
        try:
            out["fin"] = Worker("racer", db).attempt(
                "race-%02d" % i, grant_id="race-grant",
                grant_mac=grant["mac"])
        finally:
            db.close()

    ts = threading.Thread(target=do_stop)
    tf = threading.Thread(target=do_finalize)
    ts.start()
    tf.start()
    ts.join(timeout=30)
    tf.join(timeout=30)
    assert not ts.is_alive() and not tf.is_alive(), "race thread hung"

    stop_rowid = out["stop"]["stop_journal_rowid"]
    fin = out["fin"]
    label = "RACE-%02d" % i
    ev.append("STOP_ISSUED", label, {
        "new_epoch": 1, "stop_journal_rowid": stop_rowid})
    ev_decision(ev, label, fin)
    check = open_db(path, secret)
    ev_effect_check(ev, label, check, "race-%02d" % i)
    check.close()

    forbidden = (fin["decision"] == "ADMIT"
                 and fin["journal_rowid"] > stop_rowid)
    winner = "STOP" if stop_rowid < fin["journal_rowid"] else "FINALIZE"
    return winner, forbidden


def run_races(ev):
    winners = {"STOP": 0, "FINALIZE": 0}
    forbidden = 0
    for i in range(20):
        winner, bad = race_trial(i, ev)
        winners[winner] += 1
        forbidden += 1 if bad else 0
    return winners, forbidden


# ---- main ----------------------------------------------------------------
def main():
    os.makedirs(WORK, exist_ok=True)
    os.makedirs(EVDIR, exist_ok=True)
    ev = EvidenceLog(os.path.join(EVDIR, "evidence.jsonl"))
    for fn in (path_p1, path_p2, path_p3, path_p4, path_p5, path_p6, path_p7,
               control_b, control_c, control_d, control_e, control_f):
        fn(ev)
    ev.close()

    rev = EvidenceLog(os.path.join(EVDIR, "race_evidence.jsonl"))
    winners, forbidden = run_races(rev)
    rev.close()

    print("paths+controls evidence: %s" % os.path.join(EVDIR, "evidence.jsonl"))
    print("race evidence: %s" % os.path.join(EVDIR, "race_evidence.jsonl"))
    print("race winners: STOP=%d FINALIZE=%d forbidden=%d"
          % (winners["STOP"], winners["FINALIZE"], forbidden))
    assert forbidden == 0, "FORBIDDEN ORDERING OBSERVED"
    print("race invariant holds: 0 forbidden orderings in 20 trials")


if __name__ == "__main__":
    main()
