#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/_common.sh"
cd "$ROOT"

export PYTHONPATH="$ROOT"
exec "$PYTHON" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
