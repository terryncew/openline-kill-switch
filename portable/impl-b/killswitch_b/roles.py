"""Actor roles. The authority boundary is structural:

- Owner is constructed WITH the owner secret and is the only role whose
  methods call GateDB.owner_*.
- Worker and Receiver are constructed WITHOUT the secret and expose NO
  method that mutates STOP state. There is no code path on them capable of
  issuing, clearing, restoring, decreasing, or advancing STOP authority.

Receiver.local_epoch is a deliberately stale-able local cache (P6). It is
never consulted by the final gate; GateDB.finalize() always reads the
authoritative stop_state row inside its own transaction.
"""

from .store import GateDB


class Owner:
    def __init__(self, db, owner_secret):
        self._db = db
        self._secret = owner_secret

    def issue_stop(self):
        return self._db.owner_issue_stop(self._secret)

    def clear_stop(self):
        return self._db.owner_clear_stop(self._secret)

    def create_grant(self, grant_id):
        return self._db.owner_create_grant(self._secret, grant_id)

    def revoke_grant(self, grant_id):
        return self._db.owner_revoke_grant(self._secret, grant_id)


class Worker:
    """A worker can attempt protected consequences; it cannot touch STOP."""

    def __init__(self, name, db):
        self.name = name
        self._db = db

    def attempt(self, action_id, grant_id=None, grant_mac=None):
        return self._db.finalize(action_id, self.name,
                                 grant_id=grant_id, grant_mac=grant_mac)


class Receiver:
    """A receiver admits work preliminarily (non-authoritative) and runs the
    final gate. Its local_epoch cache may go stale; staleness never grants
    authority because finalize() reads authoritative state itself."""

    def __init__(self, name, db):
        self.name = name
        self._db = db
        self.local_epoch = None  # unknown until first sync

    def sync(self):
        """Refresh the local epoch cache from the authoritative store."""
        self.local_epoch = self._db.read_stop()["epoch"]
        return self.local_epoch

    def preliminary(self, action_id):
        return self._db.preliminary_admit(action_id, self.name)

    def finalize(self, action_id, grant_id=None, grant_mac=None):
        return self._db.finalize(action_id, self.name,
                                 grant_id=grant_id, grant_mac=grant_mac)

    def restore_stale_snapshot(self, snapshot_db):
        """Restore receiver-local belief from a stale snapshot copy.
        This changes only the receiver's local cache, never the
        authoritative store."""
        self.local_epoch = snapshot_db.read_stop()["epoch"]
        return self.local_epoch


def open_db(path, owner_secret):
    return GateDB(path, owner_secret)
