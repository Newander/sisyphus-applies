# Local Job Search Tracker

A local single-user app for tracking a job search. Stores everything on your own machine — no cloud, no auth, no SaaS.

## What it does

- Track companies and job applications with a full status history.
- Attach documents (CV, cover letters) to applications.
- Extract job posting data from a URL or pasted text via the Codex CLI bridge.
- Generate cover letters through the same bridge.
- Dashboard with application stats, timeline chart, and recent activity.

## Tech stack

- **Frontend** — Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn/ui
- **Backend** — FastAPI, SQLAlchemy 2, psycopg3, Alembic
- **Database** — PostgreSQL (local)
- **Worker** — APScheduler

## Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 14+

## Local run

### First time

**Linux / macOS**
```bash
./scripts/setup.sh
```

**Windows (PowerShell)**
```powershell
.\scripts\setup.ps1
```

The script checks prerequisites, creates `.env` from `.env.example`, installs dependencies, applies migrations, and optionally seeds demo data. Edit `.env` beforehand if your PostgreSQL credentials differ from the defaults (`postgres/postgres` on `localhost:5432`).

### After setup

```bash
./scripts/start-all.sh        # Linux / macOS
.\scripts\start-all.ps1       # Windows
```

`start-all` launches the backend, worker, and frontend in the background and writes logs to `logs/`. Ctrl+C stops all three.

Frontend: `http://localhost:9001` · Backend API: `http://127.0.0.1:9002`

## Codex bridge

`POST /api/codex/ask` spawns the local Codex CLI from the project root, passes a prompt via stdin, and returns stdout. Two modes:

- `text` — pass context directly.
- `url` — scrape visible text from the given URL first, then pass it to Codex.

Configured via `.env`:

```dotenv
CODEX_CLI_COMMAND=codex
CODEX_CLI_ARGS=exec -
CODEX_CLI_TIMEOUT_SECONDS=120
```

On Windows, if `codex.exe` from WindowsApps is not allowed to run, point `CODEX_CLI_COMMAND` to a working binary or a PowerShell wrapper.
