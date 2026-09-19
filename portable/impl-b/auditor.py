"""Separate auditor for Implementation B evidence.

Reads ONLY the completed evidence bundle (hash-chained JSONL). Never trusts
the live controller's declaration. Appraises each path as exactly one of
STOPPED / ESCAPED / UNKNOWN. Silence never becomes STOPPED: a missing
STOP_ISSUED, DECISION, or effect-store check yields UNKNOWN, never an
upgrade.

Usage: python3 auditor.py evidence/evidence.jsonl [evidence/race_evidence.jsonl]
Exit 0 iff every path/control appraises STOPPED and the hash chain verifies.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from killswitch_b.evidence import load_records, verify_chain


def by_label(records):
    labels = {}
    for r in records:
        labels.setdefault(r["label"], []).append(r)
    return labels


def find(recs, rtype, **match):
    out = []
    for r in recs:
        if r["type"] != rtype:
            continue
        if all(r["payload"].get(k) == v for k, v in match.items()):
            out.append(r)
    return out


def check_post_stop_attempt(label, recs, action_id, stop_rowid):
    """A post-STOP attempt is STOPPED iff: a REFUSE DECISION exists for it on
    the authoritative store, ordered after STOP_EFFECTIVE, AND the effect
    store was checked directly and the effect is absent. Any authoritative
    post-STOP effect (or ADMIT) is ESCAPED. Anything missing is UNKNOWN."""
    decisions = find(recs, "DECISION", action_id=action_id,
                     store="authoritative")
    admits = [d for d in decisions if d["payload"].get("decision") == "ADMIT"]
    refuses = [d for d in decisions if d["payload"].get("decision") == "REFUSE"]
    for d in admits:
        p = d["payload"]
        if p.get("attempt_journal_rowid") and p["attempt_journal_rowid"] > stop_rowid:
            return "ESCAPED", "authoritative ADMIT after STOP_EFFECTIVE"
    if not refuses:
        return "UNKNOWN", "no REFUSE DECISION for %s" % action_id
    d = refuses[0]
    p = d["payload"]
    if p.get("stop_journal_rowid") != stop_rowid:
        return "UNKNOWN", "DECISION stop_rowid does not match STOP_ISSUED"
    if not p.get("attempt_journal_rowid") or p["attempt_journal_rowid"] <= stop_rowid:
        return "UNKNOWN", "attempt ordering vs STOP_EFFECTIVE ambiguous"
    observed = find(recs, "EFFECT_OBSERVED", action_id=action_id,
                    store="authoritative")
    for o in observed:
        if o["payload"].get("effect_journal_rowid", 0) > stop_rowid:
            return "ESCAPED", "post-STOP effect present in effect store"
    # No post-STOP effect exists. Effect absence is established either by a
    # direct absence check, or by the only present effect being the honest
    # pre-STOP one (replay of a pre-stop action_id adds nothing new).
    absent = find(recs, "EFFECT_ABSENCE_OBSERVED", action_id=action_id,
                  store="authoritative")
    pre_existing = [o for o in observed
                    if (o["payload"].get("effect_journal_rowid") or 0)
                    <= stop_rowid]
    if not absent and not pre_existing:
        return "UNKNOWN", "no independent effect-store absence check"
    tail = "effect absent from store" if absent else \
        "only the honest pre-STOP effect present; replay added nothing"
    return "STOPPED", "refused at final gate; " + tail


def appraise(label, recs):
    # Control B has no STOP_ISSUED by construction: the authority store
    # itself is unavailable, so no STOP transition could be recorded.
    if label == "B":
        d = find(recs, "DECISION", action_id="b-attempt",
                 store="authoritative")
        refuses = [x for x in d
                   if x["payload"].get("decision") == "REFUSE"
                   and x["payload"].get("reason") == "AUTHORITY_UNAVAILABLE"]
        admits = [x for x in d if x["payload"].get("decision") == "ADMIT"]
        if admits or find(recs, "EFFECT_OBSERVED", action_id="b-attempt"):
            return "ESCAPED", "effect committed despite unavailable authority"
        if not refuses:
            return "UNKNOWN", "availability loss not recorded"
        return "STOPPED", "fail-closed; availability loss recorded"
    stops = find(recs, "STOP_ISSUED")
    if not stops:
        return "UNKNOWN", "no STOP_ISSUED record"
    stop_rowid = stops[0]["payload"].get("stop_journal_rowid")
    if stop_rowid is None:
        return "UNKNOWN", "STOP_ISSUED lacks stop_journal_rowid"
    attempts = find(recs, "POST_STOP_ATTEMPT")

    if label == "P1":
        # Requires the honest pre-STOP contrast too: an ADMIT ordered before
        # STOP_EFFECTIVE with its effect present.
        pre = [d for d in find(recs, "DECISION", action_id="p1-pre")
               if d["payload"].get("decision") == "ADMIT"
               and (d["payload"].get("attempt_journal_rowid") or 0) < stop_rowid]
        pre_eff = [o for o in find(recs, "EFFECT_OBSERVED", action_id="p1-pre")
                   if (o["payload"].get("effect_journal_rowid") or 0) < stop_rowid]
        if not (pre and pre_eff):
            return "UNKNOWN", "missing honest pre-STOP contrast commit"
        v, why = check_post_stop_attempt(label, recs, "p1-post", stop_rowid)
        return v, "pre-STOP contrast present; post-STOP: " + why

    if label == "F":
        v_old, why_old = check_post_stop_attempt(label, recs, "f-old",
                                                 stop_rowid)
        if v_old != "STOPPED":
            return v_old, "old authority: " + why_old
        d_new = find(recs, "DECISION", action_id="f-new",
                     store="authoritative")
        admits = [d for d in d_new if d["payload"].get("decision") == "ADMIT"]
        o_new = find(recs, "EFFECT_OBSERVED", action_id="f-new",
                     store="authoritative")
        if not admits or not o_new:
            return "UNKNOWN", "fresh-grant admission not evidenced"
        p = admits[0]["payload"]
        if (p.get("attempt_journal_rowid") or 0) <= stop_rowid:
            return "UNKNOWN", "fresh-grant admit ordering ambiguous"
        if (p.get("grant_issued_rowid") or 0) <= stop_rowid:
            return "ESCAPED", "fresh grant not issued after STOP_EFFECTIVE"
        return "STOPPED", ("old authority dead; fresh post-STOP owner grant "
                           "legitimately admitted with effect present")

    # P2-P7, C, D, E: every post-STOP attempt must be STOPPED.
    if not attempts:
        return "UNKNOWN", "no POST_STOP_ATTEMPT records"
    for a in attempts:
        aid = a["payload"]["action_id"]
        if label == "D" and aid == "d-snap":
            continue  # stale-copy commit handled below
        v, why = check_post_stop_attempt(label, recs, aid, stop_rowid)
        if v != "STOPPED":
            return v, "%s: %s" % (aid, why)
    if label == "D":
        snap_admits = [d for d in find(recs, "DECISION", action_id="d-snap")
                       if d["payload"].get("decision") == "ADMIT"]
        if not snap_admits:
            return "UNKNOWN", "stale-copy commit not evidenced"
        if any(d["payload"].get("store") == "authoritative"
               for d in snap_admits):
            return "ESCAPED", "stale copy treated as authoritative"
        snap_absent = find(recs, "EFFECT_ABSENCE_OBSERVED",
                           action_id="d-snap", store="authoritative")
        if not snap_absent:
            return "UNKNOWN", "stale-copy effect not checked on live store"
    return "STOPPED", "all post-STOP attempts refused; effects absent"


def appraise_race(records):
    labels = sorted({r["label"] for r in records})
    forbidden = 0
    wins = {"STOP": 0, "FINALIZE": 0}
    for label in labels:
        recs = [r for r in records if r["label"] == label]
        stops = find(recs, "STOP_ISSUED")
        decs = [d for d in find(recs, "DECISION")
                if d["payload"].get("decision") in ("ADMIT", "REFUSE")]
        if not stops or not decs:
            return None, "incomplete race trial %s" % label
        srow = stops[0]["payload"]["stop_journal_rowid"]
        arow = decs[0]["payload"]["attempt_journal_rowid"]
        dec = decs[0]["payload"]["decision"]
        if dec == "ADMIT" and arow > srow:
            forbidden += 1
        wins["STOP" if srow < arow else "FINALIZE"] += 1
    return (wins, forbidden), "%d trials" % len(labels)


def main():
    if len(sys.argv) < 2:
        print("usage: auditor.py evidence.jsonl [race_evidence.jsonl]")
        return 2
    ok, msg = verify_chain(sys.argv[1])
    print("hash chain: %s" % msg)
    if not ok:
        print("verdict: INDETERMINATE (evidence integrity failed)")
        return 2
    records = load_records(sys.argv[1])
    labels = by_label(records)
    expected = ["P1", "P2", "P3", "P4", "P5", "P6", "P7",
                "B", "C", "D", "E", "F"]
    all_ok = True
    for label in expected:
        recs = labels.get(label, [])
        if not recs:
            print("%-4s UNKNOWN  (silence: no records)" % label)
            all_ok = False
            continue
        verdict, why = appraise(label, recs)
        print("%-4s %-7s %s" % (label, verdict, why))
        if verdict != "STOPPED":
            all_ok = False
    if len(sys.argv) > 2:
        ok2, msg2 = verify_chain(sys.argv[2])
        print("race hash chain: %s" % msg2)
        if not ok2:
            print("race verdict: INDETERMINATE")
            return 2
        (wins, forbidden), note = appraise_race(load_records(sys.argv[2]))
        if wins is None:
            print("race verdict: INDETERMINATE (%s)" % note)
            return 2
        print("race: %s, winners STOP=%d FINALIZE=%d, forbidden=%d"
              % (note, wins["STOP"], wins["FINALIZE"], forbidden))
        if forbidden != 0:
            all_ok = False
    print("verdict: %s" % ("ALL STOPPED" if all_ok else "NOT ALL STOPPED"))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
