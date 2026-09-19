#!/bin/bash
# One-command demo run: seven-path attack suite + adversarial controls + independent audit.
# Produces the completed evidence bundle in src/, then appraises it.
set -e
cd "$(dirname "$0")/src"
PYTHONDONTWRITEBYTECODE=1 python3 run.py
