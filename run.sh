#!/usr/bin/env bash
# Launch backend + worker + frontend, stream their logs to this terminal,
# wait for Ctrl+C. Env vars are loaded from .env.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
source "$ROOT/scripts/_common.sh"
load_env

if [ -x "$ROOT/.venv/bin/python" ]; then
    PYTHON="$ROOT/.venv/bin/python"
else
    PYTHON="${PYTHON:-python3}"
fi

export PYTHONPATH="$ROOT"
export NEXT_PUBLIC_API_BASE_URL="${NEXT_PUBLIC_API_BASE_URL-http://${BACKEND_HOST:-127.0.0.1}:${BACKEND_PORT:-8000}}"

APP_ENV="${APP_ENV:-dev}"
case "$APP_ENV" in
    prod|production)
        UVICORN_RELOAD=""
        FRONTEND_CMD="run start"
        ;;
    *)
        UVICORN_RELOAD="--reload"
        FRONTEND_CMD="run dev"
        ;;
esac

if [ -t 1 ]; then
    C_BACK=$'\033[36m'; C_WORK=$'\033[33m'; C_FRONT=$'\033[35m'; C_OFF=$'\033[0m'
else
    C_BACK=""; C_WORK=""; C_FRONT=""; C_OFF=""
fi

stream() {
    local tag="$1" color="$2"
    sed -u "s/^/${color}[${tag}]${C_OFF} /"
}

pids=()
cleanup() {
    echo
    echo "Stopping..."
    for pid in "${pids[@]:-}"; do
        [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null && kill -TERM -- "-$pid" 2>/dev/null || \
            ( [ -n "$pid" ] && kill -TERM "$pid" 2>/dev/null || true )
    done
    sleep 1
    for pid in "${pids[@]:-}"; do
        [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null && kill -KILL "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

set -m

if [ "$APP_ENV" = "prod" ] || [ "$APP_ENV" = "production" ]; then
    echo "==> Building frontend (next build)"
    ( cd "$ROOT/frontend" && npm run build ) | stream build "$C_FRONT"
fi

(
    cd "$ROOT"
    exec "$PYTHON" -m uvicorn backend.main:app \
        --host "${BACKEND_HOST:-127.0.0.1}" \
        --port "${BACKEND_PORT:-8000}" \
        $UVICORN_RELOAD
) > >(stream backend "$C_BACK") 2>&1 &
pids+=($!)

(
    cd "$ROOT"
    exec "$PYTHON" -m backend.worker
) > >(stream worker "$C_WORK") 2>&1 &
pids+=($!)

(
    cd "$ROOT/frontend"
    exec npm $FRONTEND_CMD
) > >(stream frontend "$C_FRONT") 2>&1 &
pids+=($!)

echo "Mode     : $APP_ENV"
echo "Backend  : http://${BACKEND_HOST:-127.0.0.1}:${BACKEND_PORT:-8000}"
echo "Frontend : http://localhost:3000"
echo "Press Ctrl+C to stop all."

wait
