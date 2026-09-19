#!/bin/bash
# One-command verification: independent audit of the completed evidence bundle.
# Reads the bundle produced by RUN.sh. Does not trust the live controller's
# declaration that it passed: the appraiser re-derives every verdict from
# the evidence, keeps STOPPED / ESCAPED / UNKNOWN, never upgrades silence,
# and establishes effect absence from independent effect-store reads only.
# Usage: ./VERIFY.sh [evidence-bundle]   (default: src/evidence.jsonl)
set -e
cd "$(dirname "$0")/src"
BUNDLE="${1:-evidence.jsonl}"
if [ ! -f "$BUNDLE" ]; then
  echo "no bundle at $BUNDLE; running the suite first to produce it" >&2
  PYTHONDONTWRITEBYTECODE=1 python3 probes.py --summary >/dev/null
fi
PYTHONDONTWRITEBYTECODE=1 python3 audit.py "$BUNDLE"
