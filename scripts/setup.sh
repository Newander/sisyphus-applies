#!/usr/bin/env bash
# First-time setup: installs dependencies, applies migrations, and starts the app.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# ── Colour helpers ────────────────────────────────────────────────────────────
green()  { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }
red()    { printf '\033[31m%s\033[0m\n' "$*"; }
step()   { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

# ── Prerequisites ─────────────────────────────────────────────────────────────
step "Checking prerequisites"

if ! command -v python3 &>/dev/null; then
    red "Python 3.12+ is required but not found."
    exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}{sys.version_info.minor}")')
if [ "$PY_VERSION" -lt 312 ]; then
    red "Python 3.12+ is required (found $(python3 --version))."
    exit 1
fi
green "Python $(python3 --version) ✓"

if ! command -v node &>/dev/null; then
    red "Node.js 18+ is required but not found."
    exit 1
fi
green "Node.js $(node --version) ✓"

if ! command -v psql &>/dev/null; then
    yellow "psql not found — make sure PostgreSQL is running and accessible."
else
    green "PostgreSQL $(psql --version | awk '{print $3}') ✓"
fi

# ── .env ──────────────────────────────────────────────────────────────────────
step "Configuring environment"

if [ ! -f .env ]; then
    cp .env.example .env
    yellow ".env created from .env.example."
    yellow "Default credentials: postgres/postgres on localhost:5432."
    yellow "Edit .env if your PostgreSQL setup differs, then re-run this script."
    echo
    read -r -p "Press Enter to continue with the defaults, or Ctrl+C to edit .env first: "
else
    green ".env already exists ✓"
fi

# ── Backend ───────────────────────────────────────────────────────────────────
step "Installing backend dependencies"
"$ROOT/scripts/install-backend.sh"
green "Backend dependencies installed ✓"

# ── Frontend ──────────────────────────────────────────────────────────────────
step "Installing frontend dependencies"
"$ROOT/scripts/install-frontend.sh"
green "Frontend dependencies installed ✓"

# ── Database ──────────────────────────────────────────────────────────────────
step "Applying database migrations"
"$ROOT/scripts/init-db.sh"
green "Migrations applied ✓"

# ── Seed data ─────────────────────────────────────────────────────────────────
echo
read -r -p "Seed the database with demo data? [y/N] " seed
if [[ "${seed,,}" == "y" ]]; then
    step "Seeding demo data"
    "$ROOT/scripts/seed-data.sh"
    green "Demo data loaded ✓"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
printf '\n\033[1;32m Setup complete.\033[0m\n\n'
echo "Start the app:"
echo "  ./scripts/start-all.sh"
echo
echo "  Frontend → http://localhost:9001"
echo "  Backend  → http://127.0.0.1:9002"
echo
