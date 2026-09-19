"""SQLite-backed kill-switch gate (Implementation B).

Serialization mechanism: one SQLite database file. Every state change is an
ACID transaction; the shared serialization order is the journal table's
INTEGER PRIMARY KEY AUTOINCREMENT rowid (commit order), never wall-clock.

Contract mapping:
  section 1 (where STOP lives): stop_state table, single row, monotonic
      epoch (0 = ACTIVE, >=1 = STOPPED), survives restart because it is
      durable in the database file. Only Owner-role calls (guarded by the
      owner secret) can issue/clear/advance it. Worker/Receiver objects are
      never given the secret and expose no STOP-mutating method.
  section 2 (where final commit happens): GateDB.finalize() is the single
      final consequence gate. It runs ONE transaction (BEGIN IMMEDIATE)
      that reads current authoritative STOP standing and then inserts
      either the effect row (+ effects row) or the refusal row, atomically.
  section 3 (ordering): STOP_EFFECTIVE is the journal rowid of the owner
      STOP transition. BEGIN IMMEDIATE serializes STOP-vs-finalize writers
      in the database; the journal rowids record the resulting order.
  section 4 (unavailable authority): if the database cannot be opened or
      the transaction cannot run, finalize() raises and no effect row can
      exist; the harness records the availability loss as evidence.
"""

import hashlib
import hmac
import json
import sqlite3

# Study-local stand-in for credential authenticity (P3). Fixed constant so
# evidence stays deterministic across runs; NOT a real security boundary.
STUDY_CRED_KEY = b"ksa-portability-001-study-local-standin-key"

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta(
    id INTEGER PRIMARY KEY CHECK(id = 1),
    schema_v INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS stop_state(
    id INTEGER PRIMARY KEY CHECK(id = 1),
    epoch INTEGER NOT NULL,
    stop_rowid INTEGER
);
CREATE TABLE IF NOT EXISTS journal(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS grants(
    grant_id TEXT PRIMARY KEY,
    issued_rowid INTEGER NOT NULL,
    revoked INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS effects(
    action_id TEXT PRIMARY KEY,
    journal_id INTEGER NOT NULL,
    actor TEXT NOT NULL,
    detail TEXT NOT NULL
);
"""


def _mac(grant_id):
    return hmac.new(STUDY_CRED_KEY, grant_id.encode("utf-8"),
                    hashlib.sha256).hexdigest()


class GateDB:
    """One SQLite file = the shared serialization point."""

    def __init__(self, path, owner_secret):
        self.path = path
        self._owner_secret = str(owner_secret)
        # isolation_level=None -> autocommit; we manage BEGIN/COMMIT explicitly.
        # check_same_thread=False: each thread opens its own GateDB/connection.
        self.conn = sqlite3.connect(path, timeout=15, isolation_level=None,
                                    check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA busy_timeout=15000;")
        self.conn.execute("PRAGMA synchronous=FULL;")
        self.conn.executescript(SCHEMA)
        if self.conn.execute("SELECT epoch FROM stop_state WHERE id=1"
                             ).fetchone() is None:
            self.conn.execute(
                "INSERT INTO stop_state(id, epoch, stop_rowid) VALUES(1, 0, NULL)")
        if self.conn.execute("SELECT schema_v FROM meta WHERE id=1"
                             ).fetchone() is None:
            self.conn.execute("INSERT INTO meta(id, schema_v) VALUES(1, 1)")

    def close(self):
        self.conn.close()

    # ---- owner-only operations -----------------------------------------
    def _require_owner(self, secret):
        if not hmac.compare_digest(str(secret), self._owner_secret):
            raise PermissionError("STOP authority is owner-only")

    def _journal_insert(self, kind, payload):
        cur = self.conn.execute(
            "INSERT INTO journal(kind, payload) VALUES(?, ?)",
            (kind, json.dumps(payload, sort_keys=True)))
        return cur.lastrowid

    def owner_issue_stop(self, secret):
        """Owner STOP transition. Returns STOP_EFFECTIVE as journal rowid."""
        self._require_owner(secret)
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            epoch, _ = self.conn.execute(
                "SELECT epoch, stop_rowid FROM stop_state WHERE id=1").fetchone()
            new_epoch = epoch + 1
            jid = self._journal_insert("stop", {"new_epoch": new_epoch})
            self.conn.execute(
                "UPDATE stop_state SET epoch=?, stop_rowid=? WHERE id=1",
                (new_epoch, jid))
            self.conn.execute("COMMIT")
            return {"stop_journal_rowid": jid, "new_epoch": new_epoch}
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    def owner_clear_stop(self, secret):
        """Owner-only clear (contract section 1 allows owner clear)."""
        self._require_owner(secret)
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            jid = self._journal_insert("stop_clear", {"cleared_to_epoch": 0})
            self.conn.execute(
                "UPDATE stop_state SET epoch=0, stop_rowid=NULL WHERE id=1")
            self.conn.execute("COMMIT")
            return {"clear_journal_rowid": jid}
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    def owner_create_grant(self, secret, grant_id):
        """Owner-only grant. A grant issued after STOP_EFFECTIVE (issued_rowid
        greater than the STOP journal rowid) is the fresh post-stop authority
        used by control F; pre-stop grants stay dead."""
        self._require_owner(secret)
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            jid = self._journal_insert("grant", {"grant_id": grant_id})
            self.conn.execute(
                "INSERT INTO grants(grant_id, issued_rowid, revoked) "
                "VALUES(?, ?, 0)", (grant_id, jid))
            self.conn.execute("COMMIT")
            return {"grant_id": grant_id, "mac": _mac(grant_id),
                    "issued_rowid": jid}
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    def owner_revoke_grant(self, secret, grant_id):
        self._require_owner(secret)
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            jid = self._journal_insert("grant_revoke", {"grant_id": grant_id})
            self.conn.execute("UPDATE grants SET revoked=1 WHERE grant_id=?",
                              (grant_id,))
            self.conn.execute("COMMIT")
            return {"revoke_journal_rowid": jid}
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    # ---- non-authoritative preliminary admission ------------------------
    def preliminary_admit(self, action_id, actor):
        """Explicitly NON-authoritative. Returns a ticket that is not
        authority to commit; only the final gate decides."""
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            jid = self._journal_insert("preliminary",
                                       {"action_id": action_id, "actor": actor,
                                        "authoritative": False})
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise
        return {"action_id": action_id, "actor": actor,
                "authoritative": False, "preliminary_rowid": jid,
                "warning": "PRELIMINARY ONLY - not authority to commit; "
                           "the final gate decides"}

    # ---- the single final consequence gate ------------------------------
    def finalize(self, action_id, actor, grant_id=None, grant_mac=None):
        """One transaction: read current authoritative STOP standing, then
        atomically insert the effect row or the refusal row."""
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            epoch, stop_rowid = self.conn.execute(
                "SELECT epoch, stop_rowid FROM stop_state WHERE id=1"
            ).fetchone()
            if self.conn.execute(
                    "SELECT 1 FROM effects WHERE action_id=?",
                    (action_id,)).fetchone():
                jid = self._journal_insert(
                    "refuse",
                    {"action_id": action_id, "reason": "DUPLICATE_ACTION_ID",
                     "authoritative_epoch": epoch, "stop_rowid": stop_rowid})
                self.conn.execute("COMMIT")
                return self._decision("REFUSE", "DUPLICATE_ACTION_ID",
                                      action_id, actor, jid, epoch, stop_rowid,
                                      grant_id, None)
            admit, reason, mac_valid = False, None, None
            if epoch == 0:
                admit, reason = True, "ACTIVE_NO_STOP"
            elif grant_id is not None:
                row = self.conn.execute(
                    "SELECT issued_rowid, revoked FROM grants WHERE grant_id=?",
                    (grant_id,)).fetchone()
                mac_valid = hmac.compare_digest(grant_mac or "", _mac(grant_id))
                if row and not row[1] and row[0] > (stop_rowid or 0):
                    admit, reason = True, "FRESH_POST_STOP_GRANT"
                elif row:
                    reason = "OLD_AUTHORITY_DEAD"
                else:
                    reason = "UNKNOWN_GRANT"
            else:
                reason = "STOPPED_NO_GRANT"
            payload = {"action_id": action_id, "actor": actor, "reason": reason,
                       "authoritative_epoch": epoch, "stop_rowid": stop_rowid,
                       "grant_id": grant_id, "mac_valid": mac_valid}
            if admit:
                jid = self._journal_insert("effect", payload)
                self.conn.execute(
                    "INSERT INTO effects(action_id, journal_id, actor, detail)"
                    " VALUES(?, ?, ?, ?)",
                    (action_id, jid, actor,
                     json.dumps({"reason": reason}, sort_keys=True)))
                self.conn.execute("COMMIT")
                return self._decision("ADMIT", reason, action_id, actor, jid,
                                      epoch, stop_rowid, grant_id, mac_valid)
            jid = self._journal_insert("refuse", payload)
            self.conn.execute("COMMIT")
            return self._decision("REFUSE", reason, action_id, actor, jid,
                                  epoch, stop_rowid, grant_id, mac_valid)
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    @staticmethod
    def _decision(decision, reason, action_id, actor, journal_rowid, epoch,
                  stop_rowid, grant_id, mac_valid):
        return {"decision": decision, "reason": reason, "action_id": action_id,
                "actor": actor, "journal_rowid": journal_rowid,
                "epoch": epoch, "stop_rowid": stop_rowid,
                "grant_id": grant_id, "mac_valid": mac_valid}

    # ---- reads (authoritative state; used by harness, not as authority) --
    def read_stop(self):
        row = self.conn.execute(
            "SELECT epoch, stop_rowid FROM stop_state WHERE id=1").fetchone()
        return {"epoch": row[0], "stop_rowid": row[1]}

    def effect_present(self, action_id):
        return self.conn.execute(
            "SELECT 1 FROM effects WHERE action_id=?", (action_id,)).fetchone(
            ) is not None

    def effect_journal_rowid(self, action_id):
        row = self.conn.execute(
            "SELECT journal_id FROM effects WHERE action_id=?",
            (action_id,)).fetchone()
        return row[0] if row else None
