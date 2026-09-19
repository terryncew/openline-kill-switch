"""Hash-chained evidence emitter for KILL-SWITCH-REFERENCE-001.

Same chaining mechanics as the 001 study (sha256 over canonical JSON
minus prev_hash); new study name. Single-writer: the probe driver.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta

SCHEMA = "killswitch.evidence.v1"
STUDY = "KILL-SWITCH-REFERENCE-001"
BASE = datetime(2026, 9, 19, 21, 0, 0)


def _chain_hash(event: dict) -> str:
    body = {k: v for k, v in event.items() if k != "prev_hash"}
    raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


class EvidenceLog:
    def __init__(self) -> None:
        self.n = 0
        self.events: list[dict] = []
        self.prev: str | None = None

    def emit(self, path: str, event: str, detail: dict) -> dict:
        self.n += 1
        t = (BASE + timedelta(seconds=self.n)).strftime("%Y-%m-%dT%H:%M:%SZ")
        ev = {"schema": SCHEMA, "study": STUDY, "seq": self.n, "path": path,
              "event": event, "t": t, "prev_hash": self.prev, "detail": detail}
        self.prev = _chain_hash(ev)
        self.events.append(ev)
        return ev

    def write(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for ev in self.events:
                f.write(json.dumps(ev) + "\n")
