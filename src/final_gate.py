"""The final consequence boundary for KILL-SWITCH-REFERENCE-001.

Exactly one function can commit a covered effect. Every attempt runs
inside the shared store lock: it reads the CURRENT authoritative STOP
head, validates authority at the current epoch, and either refuses
(committing only the attempt record) or commits the effect. The owner
STOP transition uses the same lock, so STOP_EFFECTIVE and every effect
commit have one observable ordering.

If authoritative STOP standing cannot be established, the gate fails
closed: DENY, no effect, no cached-authority fallback.
"""
from __future__ import annotations

from dstore import DurableHeadStoreError, open_store
from worker_creds import check_worker

SERVICE_VERSION = "ksr001-ref-v1"


def finalize(path: str, action_id: str, mandate_id: str | None,
             credential: str | None, receiver_id: str) -> dict:
    """Attempt the protected effect. Returns a result dict; authority
    failures return DENY, they never raise."""
    try:
        store = open_store(path)
    except DurableHeadStoreError as exc:
        return {"decision": "REFUSE",
                "reason": "authority_unavailable_fail_closed",
                "detail": str(exc), "seq": None, "commit_seq": None,
                "stop_epoch": None}
    credential_ok = check_worker(mandate_id, credential)

    def _attempt(heads: dict) -> dict:
        seq = heads["seq"] + 1
        heads["seq"] = seq
        stop = heads["stop"]
        if any(e["action_id"] == action_id for e in heads["effects"]):
            decision, reason = "REFUSE", "duplicate_action_id"
        elif stop["standing"] != "ACTIVE":
            decision, reason = "REFUSE", "stop_effective_epoch_%d" % stop["epoch"]
        elif not credential_ok:
            decision, reason = "REFUSE", "credential_not_authentic"
        else:
            mandate = heads["mandates"].get(mandate_id)
            if mandate is None or mandate["issued_epoch"] != stop["epoch"]:
                decision, reason = "REFUSE", "authority_not_current"
            else:
                decision, reason = "ADMIT", "authority_current"
        record = {"action_id": action_id, "mandate_id": mandate_id,
                  "receiver": receiver_id, "decision": decision,
                  "reason": reason, "seq": seq, "stop_epoch": stop["epoch"]}
        heads["attempts"].append(record)
        commit_seq = None
        if decision == "ADMIT":
            commit_seq = seq
            heads["effects"].append(
                {"action_id": action_id, "mandate_id": mandate_id,
                 "receiver": receiver_id, "commit_seq": commit_seq,
                 "stop_epoch": stop["epoch"]})
        record["commit_seq"] = commit_seq
        return heads

    try:
        committed = store.read_modify_write(_attempt)
    except DurableHeadStoreError as exc:
        return {"decision": "REFUSE",
                "reason": "authority_unavailable_fail_closed",
                "detail": str(exc), "seq": None, "commit_seq": None,
                "stop_epoch": None}
    record = committed["attempts"][-1]
    return {"decision": record["decision"], "reason": record["reason"],
            "seq": record["seq"], "commit_seq": record.get("commit_seq"),
            "stop_epoch": record["stop_epoch"]}
