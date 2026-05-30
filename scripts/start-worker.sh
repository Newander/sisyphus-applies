#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/_common.sh"
cd "$ROOT"

export PYTHONPATH="$ROOT"
exec "$PYTHON" -m backend.worker
