"""Owner-controlled STOP authority for KILL-SWITCH-REFERENCE-001.

The STOP epoch lives in a durable, monotonic, lock-guarded store shared by
all receivers. Only this module (the owner role) holds the owner key and
the code paths that advance the epoch: workers and receiver processes have
no import path to either. Not possessed by workers/receivers: issue STOP,
clear STOP, decrease the epoch, restore old authority, create a successor
epoch (the last only via advance_epoch, owner-only, control F).

Credential note (labeled stand-in, KSQ-001/MRL-001 precedent): the owner
credential uses stdlib HMAC-SHA256 because the property under test is
revocation observation and commit ordering, not signature strength.
"""
from __future__ import annotations

import hashlib
import hmac

from dstore import IDENTITY, DurableHeadStore, open_store

OWNER_KEY = b"ksr001-owner-key-study-local"


def owner_credential() -> str:
    return "owner." + hmac.new(OWNER_KEY, b"stop-authority",
                               hashlib.sha256).hexdigest()


def check_owner(credential: str | None) -> bool:
    return hmac.compare_digest(credential or "", owner_credential())


def _initial_heads(mandates: dict) -> dict:
    m = {mid: {"subject": v["subject"], "scope": v["scope"],
               "issued_epoch": 0} for mid, v in mandates.items()}
    return {"stop": {"epoch": 0, "standing": "ACTIVE", "requested_seq": None,
                     "effective_seq": None},
            "seq": 0, "mandates": m, "attempts": [], "effects": []}


def create_store(path: str, mandates: dict):
    """First boot. Refuses to clobber an existing store."""
    store = DurableHeadStore.create(path, IDENTITY)

    def _init(heads: dict) -> dict:
        heads.update(_initial_heads(mandates))
        return heads

    store.read_modify_write(_init)
    return store


def issue_stop(path: str, credential: str | None) -> dict:
    """Owner STOP. Returns the committed stop head. STOP_EFFECTIVE is the
    commit of this transition; its sequence is the linearization point."""
    if not check_owner(credential):
        raise PermissionError("owner_credential_required")

    def _stop(heads: dict) -> dict:
        stop = heads["stop"]
        if stop["standing"] == "STOPPED":
            raise RuntimeError("already_stopped")
        seq = heads["seq"] + 1
        heads["seq"] = seq
        stop["epoch"] = 1
        stop["standing"] = "STOPPED"
        stop["effective_seq"] = seq
        heads["attempts"].append({"kind": "STOP_EFFECTIVE", "seq": seq})
        return heads

    return open_store(path).read_modify_write(_stop)["stop"]


def advance_epoch(path: str, credential: str | None) -> dict:
    """Control F only: deliberate owner recovery. Advances to a new ACTIVE
    epoch; pre-stop authority stays dead. Never callable by workers."""
    if not check_owner(credential):
        raise PermissionError("owner_credential_required")

    def _advance(heads: dict) -> dict:
        stop = heads["stop"]
        seq = heads["seq"] + 1
        heads["seq"] = seq
        stop["epoch"] = stop["epoch"] + 1
        stop["standing"] = "ACTIVE"
        stop["effective_seq"] = None
        heads["attempts"].append({"kind": "EPOCH_ADVANCE", "seq": seq,
                                  "epoch": stop["epoch"]})
        return heads

    return open_store(path).read_modify_write(_advance)["stop"]


def add_mandate(path: str, mandate_id: str, subject: str, scope: str) -> dict:
    def _add(heads: dict) -> dict:
        heads["mandates"][mandate_id] = {
            "subject": subject, "scope": scope,
            "issued_epoch": heads["stop"]["epoch"]}
        return heads

    return open_store(path).read_modify_write(_add)["mandates"][mandate_id]
