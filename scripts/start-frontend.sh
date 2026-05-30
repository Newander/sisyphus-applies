#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"

: "${NEXT_PUBLIC_API_BASE_URL:=http://127.0.0.1:8000}"
export NEXT_PUBLIC_API_BASE_URL

exec npm run dev
