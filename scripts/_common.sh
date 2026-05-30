#!/usr/bin/env bash
# Shared helpers for Linux/macOS scripts.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -x "$ROOT/.venv/bin/python" ]; then
    PYTHON="$ROOT/.venv/bin/python"
else
    PYTHON="${PYTHON:-python3}"
fi

load_env() {
    local env_file="$ROOT/.env"
    [ -f "$env_file" ] || return 0
    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in
            ''|\#*) continue ;;
        esac
        case "$line" in
            *=*) ;;
            *) continue ;;
        esac
        local key="${line%%=*}"
        local value="${line#*=}"
        key="${key#"${key%%[![:space:]]*}"}"
        key="${key%"${key##*[![:space:]]}"}"
        case "$key" in
            ''|*[!A-Za-z0-9_]*) continue ;;
        esac
        case "$value" in
            \"*\") value="${value%\"}"; value="${value#\"}" ;;
            \'*\') value="${value%\'}"; value="${value#\'}" ;;
            *)
                # Strip inline " # comment" only on unquoted values.
                value="${value%%[[:space:]]#*}"
                value="${value%"${value##*[![:space:]]}"}"
                ;;
        esac
        if [ -z "${!key:-}" ]; then
            export "$key=$value"
        fi
    done <"$env_file"
}

export PYTHON ROOT
