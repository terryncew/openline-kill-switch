"""Independently-running receiver process for KILL-SWITCH-REFERENCE-001.

Each receiver holds its own local cache of STOP standing in its own
memory. The cache may be stale. Preliminary (local) admission uses the
cache only and is explicitly NOT authority to commit. The only way to
commit a covered effect is final_gate.finalize(), which consults the
authoritative shared store under its lock.

This process never holds the owner key and has no code path that mutates
the STOP epoch. JSON-lines over stdin/stdout; one {"ready": ...} line at
startup (or an error line + exit 2 if authoritative state is missing).
"""
from __future__ import annotations

import argparse
import json
import sys

from dstore import DurableHeadStoreError, open_store
from final_gate import finalize


def _emit(obj: dict) -> None:
    print(json.dumps(obj), flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--store", required=True)
    args = ap.parse_args()
    try:
        cache = open_store(args.store).load()["stop"]
    except DurableHeadStoreError as exc:
        _emit({"error": "authority_unavailable_fail_closed",
               "detail": str(exc)})
        return 2
    _emit({"ready": args.id})
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        cmd = msg.get("cmd")
        if cmd == "shutdown":
            break
        elif cmd == "cache":
            _emit({"cache": cache})
        elif cmd == "refresh":
            try:
                cache = open_store(args.store).load()["stop"]
            except DurableHeadStoreError as exc:
                _emit({"error": "refresh_failed", "detail": str(exc)})
            else:
                _emit({"cache": cache})
        elif cmd == "pin_cache":
            cache = dict(msg["cache"])
            _emit({"cache": cache})
        elif cmd == "preliminary_admit":
            admitted = (cache["standing"] == "ACTIVE"
                        and bool(msg.get("mandate_id")))
            _emit({"preliminary": "ADMIT" if admitted else "REFUSE",
                   "cache_epoch": cache["epoch"],
                   "cache_standing": cache["standing"],
                   "note": "local_cache_only_not_authority"})
        elif cmd == "finalize":
            _emit(finalize(args.store, msg["action_id"],
                           msg.get("mandate_id"), msg.get("credential"),
                           args.id))
        else:
            _emit({"error": "unknown_cmd"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
