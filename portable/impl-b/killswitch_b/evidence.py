"""Hash-chained JSONL evidence log (contract section 5 vocabulary).

Each record binds the previous record's hash. No wall-clock timestamps are
written, so a deterministic run reproduces the file byte-for-byte.
"""

import hashlib
import json


def _canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


class EvidenceLog:
    GENESIS = "GENESIS"

    def __init__(self, path):
        self.path = path
        self.seq = 0
        self.prev = self.GENESIS
        self._f = open(path, "w", encoding="utf-8")

    def append(self, rtype, label, payload):
        self.seq += 1
        rec = {
            "seq": self.seq,
            "type": rtype,
            "label": label,
            "payload": payload,
            "prev": self.prev,
        }
        digest = hashlib.sha256(_canon(rec).encode("utf-8")).hexdigest()
        rec["hash"] = digest
        self._f.write(_canon(rec) + "\n")
        self._f.flush()
        self.prev = digest
        return rec

    def close(self):
        self._f.close()


def verify_chain(path):
    """Recompute every link. Returns (ok, message)."""
    prev = EvidenceLog.GENESIS
    seq = 0
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                seq += 1
                if rec.get("seq") != seq:
                    return False, "sequence break at line %d" % seq
                if rec.get("prev") != prev:
                    return False, "prev-hash break at seq %d" % seq
                claimed = rec.get("hash")
                body = {k: v for k, v in rec.items() if k != "hash"}
                if hashlib.sha256(_canon(body).encode("utf-8")).hexdigest() != claimed:
                    return False, "hash mismatch at seq %d" % seq
                prev = claimed
    except (OSError, ValueError) as exc:
        return False, "read/parse failure: %s" % exc
    return True, "chain valid, %d records" % seq


def load_records(path):
    recs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                recs.append(json.loads(line))
    return recs
