# ADR-001: Local LLM Model Selection

**Status:** Proposed  
**Date:** 2026-05-30  
**Context:** Replacing Codex CLI with a self-hosted local model via Ollama

---

## Context

The application uses Codex CLI as an AI backend for two features:

1. **Web extraction** — scrape a job posting URL, extract structured data (position, salary, requirements)
2. **Cover letter generation** — generate a cover letter from job application data

The planned expansion adds:
3. **Company research** — web search + summarize findings about a company
4. **Broad-context Q&A** — answer questions with large amounts of context (documents, history)

Requirements for the replacement:
- Runs fully locally via **Ollama**
- **Tool use / function calling** (required for web search integration)
- **Large context window** ≥ 32K (job postings can be lengthy; broad-context Q&A)
- **Streaming** responses
- Fits in **8 GB VRAM** (RTX 5070 Laptop GPU)

---

## Candidates Evaluated

| Model | Params | Context | Tool Use | VRAM @ Q4\_K\_M | Notes |
|---|---|---|---|---|---|
| **Qwen2.5 7B** | 7B | 128K | Yes | ~4.5 GB | Excellent JSON/structured output |
| **Llama 3.1 8B** | 8B | 128K | Yes | ~4.9 GB | Strong tool calling, widely tested |
| **Mistral Nemo 12B** | 12B | 128K | Yes | ~7.5 GB | Best quality in class, but tight on 8 GB |
| **Gemma 2 9B** | 9B | 8K | No | ~5.5 GB | Eliminated: no tool use, short context |
| **Phi-4 14B** | 14B | 16K | Yes | ~8.3 GB | Eliminated: exceeds 8 GB VRAM |

---

## Decision

**Model: `qwen2.5:7b` (Q4\_K\_M)**

### Rationale

**Why Qwen2.5 7B over Llama 3.1 8B:**

- Superior structured output quality. Qwen2.5 was explicitly trained on a larger instruction-following and JSON-generation dataset. This matters directly for the extraction task (parsing job postings into structured fields).
- Comparable tool use reliability. Both support Ollama's function calling protocol; Qwen2.5 7B has slightly better adherence to JSON schema constraints.
- Slightly lower VRAM footprint (4.5 GB vs 4.9 GB), leaving ~3.5 GB headroom for a 32K KV cache on an 8 GB GPU.

**Why not Mistral Nemo 12B:**

- At Q4\_K\_M requires ~7.5 GB weights alone. With a 32K KV cache (~1.5–2 GB) exceeds 8 GB, causing partial CPU offload and significant throughput drop on the RTX 5070 Laptop.

**Why not Gemma 2 9B or Phi-4:**

- Gemma 2: no tool use support — disqualified immediately.
- Phi-4: 8.3 GB model alone exceeds available VRAM.

---

## Embedding Model

For RAG (document indexing, semantic search):

**Model: `nomic-embed-text`**

- 768-dimensional embeddings
- 8K context window — sufficient for document chunks
- ~270 MB — negligible VRAM impact
- Available via Ollama, well-supported by the Python ecosystem

Vector store: **pgvector** (PostgreSQL extension) — keeps all data in the existing database, no additional infrastructure.

---

## Ollama Configuration

```
# .env additions
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_NUM_CTX=32768
```

`num_ctx=32768` balances context capacity with KV cache memory. Increase to `65536` if a use case requires it and VRAM allows.

---

## Consequences

**Positive:**
- Fully offline — no API keys, no cost per request, no data leaving the machine
- Streaming built into Ollama's API
- Tool use enables web search integration without external wrappers
- pgvector keeps the architecture simple (one DB for everything)

**Negative / tradeoffs:**
- 7B model quality is noticeably below GPT-4 class; cover letter output will require more prompt tuning
- First run requires downloading ~4.5 GB (model) + ~270 MB (embed model)
- 32K context is sufficient for most job postings but not unlimited
- Web search requires an additional tool integration (e.g., SearXNG or a free search API)
