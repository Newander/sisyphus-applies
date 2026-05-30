#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/_common.sh"
cd "$ROOT"

"$PYTHON" -m backend.sync_gmail
