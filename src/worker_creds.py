"""Worker-credential primitives (labeled HMAC stand-in).

This module is importable by receiver processes: it contains NO owner key
material and no code path that mutates the STOP epoch. The property under
test is revocation observation and commit ordering, not signature
strength (KSQ-001/MRL-001 precedent).
"""
from __future__ import annotations

import hashlib
import hmac

WORKER_KEY = b"ksr001-worker-key-study-local"


def worker_credential(mandate_id: str) -> str:
    mac = hmac.new(WORKER_KEY, mandate_id.encode(),
                   hashlib.sha256).hexdigest()
    return "%s.%s" % (mandate_id, mac)


def check_worker(mandate_id: str | None, credential: str | None) -> bool:
    if not mandate_id:
        return False
    return hmac.compare_digest(credential or "",
                               worker_credential(mandate_id))
