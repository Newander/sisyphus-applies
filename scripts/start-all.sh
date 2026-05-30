#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"

pids=()
cleanup() {
    echo
    echo "Stopping processes..."
    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

"$ROOT/scripts/start-backend.sh"  >"$LOG_DIR/backend.log"  2>&1 &
pids+=($!)
"$ROOT/scripts/start-worker.sh"   >"$LOG_DIR/worker.log"   2>&1 &
pids+=($!)
"$ROOT/scripts/start-frontend.sh" >"$LOG_DIR/frontend.log" 2>&1 &
pids+=($!)

echo "Started backend on http://127.0.0.1:9002  (logs: $LOG_DIR/backend.log)"
echo "Started frontend on http://localhost:9001 (logs: $LOG_DIR/frontend.log)"
echo "Started worker in background              (logs: $LOG_DIR/worker.log)"
echo "Press Ctrl+C to stop all."

wait
