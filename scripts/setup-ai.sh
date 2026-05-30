#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/_common.sh"
load_env

OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5:7b}"
OLLAMA_EMBED_MODEL="${OLLAMA_EMBED_MODEL:-nomic-embed-text}"
PG_DB="${POSTGRES_DB:-sisyphus_applies}"
PG_USER="${POSTGRES_USER:-postgres}"
PG_HOST="${POSTGRES_HOST:-localhost}"
PG_PORT="${POSTGRES_PORT:-5432}"

step() { echo; echo "==> $*"; }

# ── 1. Ollama ──────────────────────────────────────────────────────────────
step "Checking Ollama"
if ! command -v ollama &>/dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "Ollama $(ollama --version) already installed."
fi

step "Enabling Ollama service"
if command -v systemctl &>/dev/null; then
    systemctl --user enable --now ollama.service 2>/dev/null \
        || sudo systemctl enable --now ollama 2>/dev/null \
        || true
fi

# Give Ollama a moment to start
sleep 2
if ! ollama list &>/dev/null; then
    echo "Starting Ollama in background..."
    ollama serve &>/dev/null &
    sleep 3
fi

# ── 2. Models ──────────────────────────────────────────────────────────────
step "Pulling LLM: $OLLAMA_MODEL"
ollama pull "$OLLAMA_MODEL"

step "Pulling embedding model: $OLLAMA_EMBED_MODEL"
ollama pull "$OLLAMA_EMBED_MODEL"

# ── 3. pgvector ────────────────────────────────────────────────────────────
step "Checking pgvector PostgreSQL extension"
if psql -U "$PG_USER" -h "$PG_HOST" -p "$PG_PORT" -d "$PG_DB" \
       -c "CREATE EXTENSION IF NOT EXISTS vector;" &>/dev/null; then
    echo "pgvector extension enabled in database '$PG_DB'."
else
    echo "Could not enable pgvector automatically. You may need to install it first:"
    echo "  Arch/EndeavourOS:  yay -S pgvector  (then re-run this script)"
    echo "  Debian/Ubuntu:     sudo apt install postgresql-\$(pg_config --major-version)-pgvector"
    exit 1
fi

# ── 4. Python packages ─────────────────────────────────────────────────────
step "Installing updated Python dependencies"
"$PYTHON" -m pip install -e "$ROOT" -q

# ── Done ───────────────────────────────────────────────────────────────────
echo
echo "All done."
echo "  LLM:        $OLLAMA_MODEL"
echo "  Embeddings: $OLLAMA_EMBED_MODEL"
echo "  pgvector:   enabled in $PG_DB"
echo
echo "Add to .env if not already present:"
echo "  OLLAMA_BASE_URL=http://localhost:11434"
echo "  OLLAMA_MODEL=$OLLAMA_MODEL"
echo "  OLLAMA_EMBED_MODEL=$OLLAMA_EMBED_MODEL"
echo "  OLLAMA_NUM_CTX=32768"
