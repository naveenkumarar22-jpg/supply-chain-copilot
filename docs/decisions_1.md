# Architecture Decisions — Supply Chain Operations Copilot

## What this document is

This is the **Architecture Decision Record (ADR)** for the production rebuild of the
Supply Chain Operations Copilot. Each decision is a *rule*, grounded in the *weakness it
fixes* (or the good pattern it preserves), and pointed at *where it lives* in the
production repo.

**Status:** All decisions closed. Cleared to build.

> This file consolidates the ADR work from earlier sessions. If your working `decisions.md`
> in the repo words anything differently, treat the repo file as the source of truth and
> reconcile to it.

---

## The 13 settled decisions

| # | Decision | Rule | Fixes / Preserves | Lives in |
|---|----------|------|-------------------|----------|
| 1 | **One converged orchestrator** | A single run path where intent, retrieval, tools, memory and safety all meet. | Fixes the three parallel paths (`call_llm_safe`, `call_tool`, `agent_pipeline`) that never converged — memory & RAG never reached the final agent. | `core/orchestrator.py` |
| 2 | **LLM-driven intent routing** | The LLM classifies the query into structured fields; deterministic Python dispatches on them. | Fixes keyword `if/elif` routing that stopped at first match and hardcoded the SKU. | `core/intent.py` |
| 3 | **Tool registry + lean tools** | Tools return structured dicts, registered in a registry keyed by intent/entity. Phase 5 lean shape kept; Phase 2 intelligence (confidence flags, conflict detection) folds in as fields. | Fixes the two unreconciled tool generations (verbose vs. lean). | `core/tools/` + `registry.py` |
| 4 | **Metadata-filtered retrieval** | Filter on document metadata at search time over a larger corpus — no keyword post-filter. | Fixes the keyword post-filter bolted onto semantic search that reintroduced brittleness. | `core/retrieval.py` |
| 5 | **Persistent, session-keyed memory** | Memory survives restarts and is keyed by session. | Fixes in-RAM globals that reset on every restart. | `core/memory.py` + store |
| 6 | **Real feedback / learning** | Persist feedback; let the LLM interpret what the instruction implies; key on the situation, not exact text. | Fixes the hardcoded find-and-replace on exact query strings. | `core/feedback` (adaptive) |
| 7 | **Secrets in `.env`** | Keys rotated, loaded from `.env`, never inline; `.env` is git-ignored. | Fixes the API key pasted inline across four notebook cells. | `.env` + `config.py` |
| 8 | **Structured response contract** | Every answer returns Answer · Reasoning · Confidence · Sources · Limitations · Next Steps. | Preserves the audit-grade, decision-ready output block. | `io_contract` + orchestrator |
| 9 | **Dual-source argument resolution** | LLM's argument first, deterministic regex extraction as fallback, block if both are missing. | Preserves a genuinely good reliability pattern. | `core/intent` (arg resolution) |
| 10 | **Suggest-only validation gate** | The agent proposes, never executes; the suggest-only boundary becomes an enforced gate in the loop. | Preserves the core safety boundary. | `core/safety.py` |
| 11 | **Layered production repo** | Modules, venv, `requirements.txt`, `.env` — not notebook blocks. | Moves from a single Jupyter notebook to a coherent runtime. | repo root + folder tree |
| 12 | **FastAPI service surface** | `/query` (session-aware, returns the structured response) + `/health` + a feedback endpoint; Pydantic validation in and out. | Makes the agent a callable service, not a script. | `api/app.py` |
| 13 | **Docker + hosted UI** | A single Dockerfile, containerized, deployed with an interactive UI (Streamlit/Gradio). | Gets to a live, shareable system. | `Dockerfile` + `ui/` + host |

---

## The 3 formerly-open decisions — now closed

| Open question | Decision | Rationale |
|---------------|----------|-----------|
| **Vector store** | **FAISS**, with a thin metadata wrapper for v1 | Local, zero-infra, fast to stand up. The metadata wrapper gives you Decision #4 (metadata-filtered retrieval) without pulling in a hosted store yet. Swappable to Qdrant later behind the same `retrieval` interface. |
| **Memory backing** | **SQLite** | Satisfies Decision #5 (persistent, session-keyed memory) with a single file and no server. Honest, durable, and trivially inspectable. |
| **Project scope** | **Sample-data-first** | Build and demo against believable simulated supplier/inventory/PO data. Keeps the project fully demonstrable without a real client, which is the whole point for portfolio + interview use. |

---

## How to read this against the build

- Decisions **1–10** are the *brain* — the `core/` you build by hand, file by file.
- Decisions **11–13** are the *wrap* — repo structure, service surface, and deployment.
- The phase-by-phase runbook (Phases 0–7, ~40–55 hrs) is the execution companion to this file.
