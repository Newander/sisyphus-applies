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

"$ROOT/scripts/start-backend.sh"  > >(sed 's/^/[backend]  /' | tee "$LOG_DIR/backend.log") 2>&1 &
pids+=($!)
"$ROOT/scripts/start-worker.sh"   > >(sed 's/^/[worker]   /' | tee "$LOG_DIR/worker.log")  2>&1 &
pids+=($!)
"$ROOT/scripts/start-frontend.sh" > >(sed 's/^/[frontend] /' | tee "$LOG_DIR/frontend.log") 2>&1 &
pids+=($!)

echo "[start-all] backend  → http://127.0.0.1:9002"
echo "[start-all] frontend → http://localhost:9001"
echo "[start-all] Press Ctrl+C to stop all."

wait
