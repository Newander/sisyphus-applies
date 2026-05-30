# Sisyphus Applies

A local-first, single-user job search tracker with an embedded AI assistant powered by a local LLM. No cloud, no API keys, no data leaving your machine.

Built as a portfolio project demonstrating a full-stack AI application with RAG, streaming inference, and tool use — all running entirely offline.

---

## Features

**Job search tracking**
- Companies and applications with a full status history and transition graph
- Document storage — attach CVs and cover letters to applications
- Dashboard with application timeline, stats, and recent activity

**Local AI assistant**
- Ask questions about job postings — paste text or give a URL to scrape
- Answers draw on your own stored data via **RAG** (Retrieval-Augmented Generation)
- **Web search** via tool use (DuckDuckGo) for live company research
- **Streaming responses** — text appears token-by-token via SSE
- **Cover letter generation** from application data
- Provider abstraction — swap between local Ollama and Codex CLI via one env var

**AI infrastructure**
- Embeddings with `nomic-embed-text` stored in **pgvector**
- Automatic indexing of applications, companies, and uploaded documents on save
- Startup check indexes any records that were missed
- Reindex button in the UI

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Browser (9001)                       │
│              Next.js 15 · React 19 · shadcn/ui           │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP / SSE
┌───────────────────────▼─────────────────────────────────┐
│                   Backend (9002)                          │
│              FastAPI · SQLAlchemy 2 · psycopg3            │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  REST API   │  │  RAG service │  │  LLM provider  │  │
│  │ /api/...    │  │  pgvector    │  │  abstraction   │  │
│  └─────────────┘  └──────┬───────┘  └───────┬────────┘  │
└─────────────────────────┼───────────────────┼───────────┘
                          │                   │
              ┌───────────▼───┐     ┌─────────▼──────────┐
              │  PostgreSQL   │     │   Ollama (11434)    │
              │  + pgvector   │     │  qwen2.5:7b         │
              │  sisyphus_    │     │  nomic-embed-text   │
              │  applies      │     │  + web search tool  │
              └───────────────┘     └────────────────────┘
```

**Three processes run together:**
- **Frontend** — Next.js dev server at `http://localhost:9001`
- **Backend** — FastAPI + Alembic at `http://127.0.0.1:9002`
- **Worker** — APScheduler background jobs

---

## Tech stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | Next.js 15, React 19, TypeScript | App Router, Server Components, type safety |
| UI | Tailwind CSS, shadcn/ui | Consistent design system, no runtime CSS |
| Backend | FastAPI, Python 3.12 | Async-first, automatic OpenAPI, type hints |
| ORM | SQLAlchemy 2 + psycopg3 | Typed queries, async sessions, pgvector support |
| Migrations | Alembic | Schema versioning, auto-generate from models |
| Database | PostgreSQL + pgvector | Relational + vector search in one place |
| LLM runtime | Ollama | Local model serving with tool use and streaming |
| Embeddings | nomic-embed-text | 768-dim, fast, runs on CPU or GPU |
| Web scraping | Playwright | JavaScript-rendered pages |

---

## Prerequisites

- **Python 3.12+**
- **Node.js 18+**
- **PostgreSQL 14+**
- **Ollama** — [ollama.com](https://ollama.com)

---

## Quick start

### 1. Clone and set up

```bash
git clone https://github.com/newander/sisyphus-applies.git
cd sisyphus-applies
./scripts/setup.sh          # Linux / macOS
.\scripts\setup.ps1         # Windows (PowerShell)
```

The setup script checks prerequisites, creates `.env` from `.env.example`, installs Python and Node dependencies, applies database migrations, and optionally seeds demo data.

Edit `.env` if your PostgreSQL credentials differ from the defaults (`postgres/postgres` on `localhost:5432`).

### 2. Set up the AI components

```bash
./scripts/setup-ai.sh
```

Installs Ollama, pulls `qwen2.5:7b` and `nomic-embed-text`, enables the `pgvector` extension.

### 3. Run

```bash
./scripts/start-all.sh      # Linux / macOS
.\scripts\start-all.ps1     # Windows
```

Opens at **http://localhost:9001**

---

## Configuration

Key `.env` variables:

```dotenv
# LLM provider: "ollama" (local) or "codex" (Codex CLI)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_NUM_CTX=32768

# Web search via DuckDuckGo tool use
WEB_SEARCH_ENABLED=true
```

---

## Development

```bash
# Backend (with auto-reload)
.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 9002 --reload --reload-dir backend

# Frontend
cd frontend && npm run dev

# Migrations
make alembic-upgrade
make alembic-revision m="describe change"

# Lint
.venv/bin/ruff check backend/
cd frontend && npm run lint

# Tests
.venv/bin/pytest backend/tests/
```

---

## License

[MIT](LICENSE)
