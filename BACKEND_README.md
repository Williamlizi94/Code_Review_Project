# CodeGuardian AI — Backend Documentation

> Intelligent Code Review Agent powered by LLM + Static Analysis + RAG

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Architecture Design](#architecture-design)
- [Review Workflow](#review-workflow)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Getting Started](#getting-started)
- [Configuration](#configuration)

---

## Overview

The CodeGuardian AI backend is a Python-based asynchronous service that orchestrates a multi-stage code review pipeline. It combines three analysis layers:

| Layer | Description |
|---|---|
| **Rule Engine** | Semgrep + language-specific linters run statically on source code |
| **LLM Reasoning** | LangGraph ReAct agent powered by `gpt-5.4-mini` performs semantic, contextual analysis |
| **RAG Augmentation** | Historical defects and coding standards retrieved from a vector knowledge base to enrich LLM context |

The system exposes a REST API for submitting reviews, retrieving results, managing the knowledge base, and receiving webhook events from GitHub, GitLab, and Bitbucket.

---

## Tech Stack

| Category | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.12 | Primary runtime |
| **Web Framework** | FastAPI + Uvicorn | Async REST API server |
| **AI Agent** | LangChain + LangGraph | ReAct agent orchestration |
| **LLM** | OpenAI `gpt-5.4-mini` | Code reasoning and fix suggestions |
| **Embeddings** | OpenAI `text-embedding-3-small` | 1536-dim vector representations |
| **Static Analysis** | Semgrep | 30+ language rule-based scanner |
| **Python Linter** | Bandit | Python security vulnerability detection |
| **JS/TS Linter** | ESLint | JavaScript / TypeScript quality checks |
| **Go Linter** | Staticcheck | Go static analysis |
| **AST Parsing** | Tree-sitter | Language-agnostic AST extraction |
| **RAG Retrieval** | BM25 (rank-bm25) + pgvector | Hybrid keyword + semantic search |
| **Reranking** | sentence-transformers Cross-Encoder | Precision reranking of RAG results |
| **Task Queue** | Celery + Redis | Async pipeline execution |
| **Database** | PostgreSQL 16 + pgvector | Metadata storage + vector embeddings |
| **Migrations** | Alembic | Database schema version management |
| **File Storage** | MinIO / AWS S3 | Report and document storage |
| **Auth** | JWT (python-jose) + bcrypt (passlib) | Stateless authentication |
| **Git Operations** | GitPython + PyGithub + python-gitlab | Repo clone, diff, PR comment writing |
| **Report Generation** | Jinja2 + WeasyPrint | HTML / Markdown / PDF reports |
| **HTTP Client** | httpx | Async webhook callbacks |
| **Logging** | Loguru | Structured, coloured logs |
| **Containerization** | Docker + Docker Compose | Infrastructure and deployment |
| **Testing** | pytest + pytest-asyncio | Unit and integration tests |

---

## Architecture Design

```
┌─────────────────────────────────────────────────────────────────┐
│                         Access Layer                            │
│          REST API Client   Git Webhook   CI/CD Pipeline         │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                    Gateway & Auth Layer                          │
│               FastAPI Router  ·  JWT Bearer Auth                 │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                       Core Service Layer                         │
│                                                                 │
│   ┌──────────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│   │  Review Service  │  │  Git Service │  │  Report Service │  │
│   │  (Celery Tasks)  │  │  (GitPython) │  │  (Jinja2/PDF)   │  │
│   └────────┬─────────┘  └──────────────┘  └─────────────────┘  │
│            │                                                    │
│   ┌────────▼──────────────────────────────────────────────┐    │
│   │            LangGraph AI Agent (ReAct Loop)             │    │
│   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │    │
│   │   │  LLM Client │  │ Tool Nodes  │  │   Prompt    │   │    │
│   │   │(gpt-5.4-mini│  │(Semgrep/AST)│  │   Builder   │   │    │
│   │   └─────────────┘  └─────────────┘  └─────────────┘   │    │
│   └───────────────────────────────────────────────────────┘    │
│                                                                 │
│   ┌───────────────────────────────────────────────────────┐    │
│   │                      RAG Engine                        │    │
│   │   Knowledge Mgmt  ·  BM25+pgvector Hybrid Search  ·   │    │
│   │                   Cross-Encoder Rerank                 │    │
│   └───────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                      Data Infrastructure                         │
│                                                                 │
│   PostgreSQL + pgvector      Redis            MinIO / S3         │
│   (metadata + vectors)    (queue/cache)     (file storage)       │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                        AI Model Layer                            │
│              OpenAI gpt-5.4-mini  ·  text-embedding-3-small      │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

**Async-first** — FastAPI + SQLAlchemy async + httpx ensures non-blocking I/O throughout.

**Celery for heavy lifting** — The review pipeline can take minutes. Celery offloads this from the HTTP request cycle, with Redis as both broker and result backend.

**Dual-engine analysis** — Static analyzers (deterministic, fast, language-specific) run first and provide grounded evidence. The LLM agent then reasons over those results along with the RAG context, reducing hallucinations and false positives.

**Tool-driven agent** — The LangGraph `create_react_agent` pattern ensures the LLM calls verifiable local tools (`run_semgrep`, `parse_ast`, `run_linters`, `get_git_diff`) before drawing conclusions, keeping outputs trustworthy.

**RRF fusion for RAG** — Reciprocal Rank Fusion combines BM25 keyword rankings and pgvector cosine similarity rankings, balancing lexical precision with semantic recall.

---

## Review Workflow

The review pipeline is a sequential chain of 8 stages. Each stage receives and mutates a shared `PipelineContext` object.

```
ReviewRequest (API / Webhook)
        │
        ▼
┌───────────────────────────────────────────────────┐
│  Stage 1 │ GitCloneStage                          │
│           │ Clone or pull the target repository   │
│           │ via GitPython. Writes workspace_path. │
└─────────────────────────┬─────────────────────────┘
                          │
┌─────────────────────────▼─────────────────────────┐
│  Stage 2 │ StaticAnalysisStage                    │
│           │ Run Semgrep + language-specific        │
│           │ linters in parallel (asyncio.gather).  │
│           │ Produces: static_issues[]              │
└─────────────────────────┬─────────────────────────┘
                          │
┌─────────────────────────▼─────────────────────────┐
│  Stage 3 │ ASTParseStage                          │
│           │ Structural analysis delegated to the   │
│           │ parse_ast tool inside the agent loop.  │
└─────────────────────────┬─────────────────────────┘
                          │
┌─────────────────────────▼─────────────────────────┐
│  Stage 4 │ RAGRetrievalStage                      │
│           │ Build query from top static issues.    │
│           │ BM25 + pgvector hybrid search → RRF    │
│           │ fusion → Cross-Encoder rerank.         │
│           │ Produces: rag_context (top-5 chunks)   │
└─────────────────────────┬─────────────────────────┘
                          │
┌─────────────────────────▼─────────────────────────┐
│  Stage 5 │ LLMReviewStage                         │
│           │ LangGraph ReAct agent:                 │
│           │   1. Receives system prompt + code     │
│           │   2. Calls tools autonomously          │
│           │   3. Synthesises findings + suggestions│
│           │ Produces: llm_issues[]                 │
└─────────────────────────┬─────────────────────────┘
                          │
┌─────────────────────────▼─────────────────────────┐
│  Stage 6 │ ResultMergeStage                       │
│           │ Deduplicate by (file, line, rule_id).  │
│           │ Prefer LLM issues when duplicates      │
│           │ exist (they carry fix suggestions).    │
│           │ Sort by severity: CRITICAL→HIGH→…      │
│           │ Produces: merged_issues[]              │
└─────────────────────────┬─────────────────────────┘
                          │
┌─────────────────────────▼─────────────────────────┐
│  Stage 7 │ ReportGenerateStage                    │
│           │ Render Jinja2 HTML report (interactive │
│           │ severity cards + issue table).         │
│           │ Render Markdown report.                │
│           │ PDF via WeasyPrint (optional).         │
└─────────────────────────┬─────────────────────────┘
                          │
┌─────────────────────────▼─────────────────────────┐
│  Stage 8 │ NotifyStage                            │
│           │ POST review summary to notify_webhook. │
│           │ Write inline PR/MR comments via        │
│           │ PyGithub / python-gitlab.              │
└───────────────────────────────────────────────────┘
        │
        ▼
  Persist to PostgreSQL
  (ReviewIssue rows + ReviewReport rows)
  Update Review.status → COMPLETED / FAILED
```

### LangGraph Agent Tools

| Tool | Description |
|---|---|
| `run_semgrep` | Run Semgrep with specified ruleset on a path |
| `parse_ast` | Tree-sitter AST parse — extract functions, classes, complexity |
| `run_linters` | Language-specific linter (Bandit / ESLint / Staticcheck) |
| `get_git_diff` | Get unified diff between two git refs |

### RAG Hybrid Search

```
Query
  │
  ├─► BM25 (rank-bm25)
  │     Tokenise query → score all corpus chunks → top-K ranked list
  │
  ├─► pgvector cosine similarity
  │     Embed query (text-embedding-3-small) → ANN search → top-K ranked list
  │
  └─► RRF Fusion (k=60)
        score(d) = Σ 1 / (k + rank_i(d))
        Combined ranking → Cross-Encoder rerank → Final top-5
```

---

## Project Structure

```
codeguardian-ai/
│
├── app/
│   ├── main.py                     # FastAPI app factory, lifespan, CORS
│   ├── config.py                   # pydantic-settings (env-driven config)
│   ├── database.py                 # Async SQLAlchemy engine + session
│   ├── worker.py                   # Celery app + run_review_task
│   │
│   ├── models/                     # SQLAlchemy ORM models
│   │   ├── base.py                 # DeclarativeBase + TimestampMixin + UUIDMixin
│   │   ├── user.py                 # User
│   │   ├── review.py               # Review, ReviewIssue, ReviewReport
│   │   ├── knowledge.py            # KnowledgeDocument, KnowledgeChunk
│   │   └── audit.py                # AuditLog
│   │
│   ├── schemas/                    # Pydantic request / response schemas
│   │   ├── review.py               # ReviewRequest, ReviewResponse, IssueOut
│   │   ├── knowledge.py            # KnowledgeUploadRequest, SearchResult
│   │   └── user.py                 # UserCreate, Token, LoginRequest
│   │
│   ├── auth/
│   │   └── service.py              # JWT sign/verify, bcrypt hashing, get_current_user
│   │
│   ├── routers/                    # FastAPI routers (one per domain)
│   │   ├── auth.py                 # POST /auth/register, /auth/login, GET /auth/me
│   │   ├── reviews.py              # POST /reviews, GET /reviews/{id}, GET /reviews/{id}/report
│   │   ├── knowledge.py            # POST /knowledge/upload, GET /knowledge/search
│   │   └── webhooks.py             # POST /webhook/github, /gitlab, /bitbucket
│   │
│   ├── analyzer/                   # Static analyzer wrappers (subprocess-based)
│   │   ├── base.py                 # AnalyzerIssue dataclass, BaseAnalyzer ABC
│   │   ├── semgrep.py              # Semgrep JSON output parser
│   │   ├── bandit.py               # Bandit (Python security)
│   │   ├── eslint.py               # ESLint (JS / TS)
│   │   └── staticcheck.py          # Staticcheck (Go)
│   │
│   ├── agent/                      # LangGraph AI Agent
│   │   ├── graph.py                # create_react_agent + gpt-5.4-mini binding
│   │   ├── tools/
│   │   │   ├── semgrep_tool.py     # @tool run_semgrep
│   │   │   ├── tree_sitter_tool.py # @tool parse_ast
│   │   │   ├── linters_tool.py     # @tool run_linters
│   │   │   └── git_diff_tool.py    # @tool get_git_diff
│   │   └── prompts/
│   │       └── review_prompt.py    # Jinja2 system + user prompt builder
│   │
│   ├── rag/                        # RAG engine
│   │   ├── embeddings.py           # OpenAI text-embedding-3-small wrapper
│   │   ├── knowledge.py            # Document chunking + pgvector ingestion
│   │   ├── hybrid_search.py        # BM25 + pgvector + RRF fusion
│   │   └── rerank.py               # Cross-Encoder reranker (sentence-transformers)
│   │
│   ├── git/
│   │   └── service.py              # clone_or_pull, get_diff, write_pr_comments
│   │
│   ├── review/                     # Review pipeline orchestration
│   │   ├── service.py              # run_review_pipeline — assembles and runs stages
│   │   ├── merger.py               # Deduplication + severity sorting
│   │   └── pipeline/
│   │       ├── base.py             # PipelineStage ABC + PipelineContext dataclass
│   │       ├── git_clone.py        # Stage 1
│   │       ├── static_analysis.py  # Stage 2
│   │       ├── ast_parse.py        # Stage 3
│   │       ├── rag_retrieval.py    # Stage 4
│   │       ├── llm_review.py       # Stage 5
│   │       ├── result_merge.py     # Stage 6
│   │       ├── report_generate.py  # Stage 7
│   │       └── notify.py           # Stage 8
│   │
│   ├── report/                     # Report generators
│   │   ├── html.py                 # Jinja2 interactive HTML report
│   │   ├── markdown.py             # Markdown report
│   │   └── pdf.py                  # WeasyPrint PDF (optional)
│   │
│   └── webhook/                    # Webhook signature verification + event routing
│       ├── github.py               # X-Hub-Signature-256 (HMAC-SHA256)
│       ├── gitlab.py               # X-Gitlab-Token
│       └── bitbucket.py            # X-Hub-Signature (HMAC-SHA256)
│
├── migrations/                     # Alembic async migrations
│   ├── env.py                      # Async Alembic environment
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial_schema.py   # Full schema + pgvector extension + IVFFlat index
│
├── tests/
│   ├── conftest.py                 # Shared fixtures (in-memory SQLite, test client)
│   ├── unit/
│   │   ├── test_merger.py          # Dedup / severity sorting logic
│   │   └── test_analyzer.py        # Semgrep / Bandit JSON parsing (subprocess mocked)
│   └── integration/
│       └── test_review_api.py      # Full API flow (register → login → submit → list)
│
├── docker/
│   ├── compose-dev.yml             # PostgreSQL+pgvector, Redis, MinIO
│   └── compose-prod.yml            # Full production deployment (api + worker + infra)
│
├── pyproject.toml                  # Poetry dependency management
├── alembic.ini                     # Alembic configuration
└── .env.example                    # Environment variable template
```

---

## API Reference

### Auth

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Register a new user |
| `POST` | `/api/v1/auth/login` | Login and receive JWT token |
| `GET` | `/api/v1/auth/me` | Get current user profile |

### Reviews

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/reviews` | Submit a review task (async, returns 202) |
| `GET` | `/api/v1/reviews` | List review history (paginated, filterable) |
| `GET` | `/api/v1/reviews/{id}` | Get review status and all issues |
| `GET` | `/api/v1/reviews/{id}/report?format=html\|markdown\|pdf` | Download report |

**Review types:** `GIT_REPO` · `DIRECTORY` · `FILE` · `SNIPPET`

**Review modes:** `FULL` · `INCREMENTAL` (git diff only)

### Knowledge Base

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/knowledge/upload` | Upload a document (async vectorization) |
| `GET` | `/api/v1/knowledge/search?q=...` | Hybrid search with optional reranking |
| `GET` | `/api/v1/knowledge/documents` | List all documents |
| `DELETE` | `/api/v1/knowledge/documents/{id}` | Delete a document and its chunks |

### Webhooks

| Method | Endpoint | Platform |
|---|---|---|
| `POST` | `/api/v1/webhook/github` | GitHub push / pull_request events |
| `POST` | `/api/v1/webhook/gitlab` | GitLab push / merge_request events |
| `POST` | `/api/v1/webhook/bitbucket` | Bitbucket push / pullrequest events |

Full Swagger UI available at `/docs` after startup.

---

## Getting Started

### 1. Start Infrastructure

```bash
docker compose -f docker/compose-dev.yml up -d
```

This starts:
- **PostgreSQL 16 + pgvector** on port `5432`
- **Redis 7** on port `6379`
- **MinIO** on port `9000` (console: `9001`)

### 2. Install Dependencies

```bash
pip install poetry
poetry install
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env — at minimum set OPENAI_API_KEY
```

### 4. Run Database Migrations

```bash
poetry run alembic upgrade head
```

### 5. Start the API Server

```bash
poetry run uvicorn app.main:app --reload --port 8080
```

### 6. Start the Celery Worker

```bash
poetry run celery -A app.worker worker --loglevel=info
```

### 7. Run Tests

```bash
poetry run pytest tests/ -v
```

Visit `http://localhost:8080/docs` for the interactive Swagger UI.

---

## Configuration

Key environment variables (see [.env.example](.env.example) for full list):

```env
# LLM
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.4-mini

# Database
DATABASE_URL=postgresql+asyncpg://codeguardian:codeguardian@localhost:5432/codeguardian

# Redis / Celery
REDIS_URL=redis://localhost:6379/0

# Auth
JWT_SECRET=change-me-in-production

# Analyzer toggles
ANALYZER_SEMGREP_ENABLED=true
ANALYZER_BANDIT_ENABLED=true
ANALYZER_ESLINT_ENABLED=true
ANALYZER_STATICCHECK_ENABLED=true

# Quality gate (block CI if thresholds exceeded)
QUALITY_GATE_ENABLED=false
QUALITY_GATE_FAIL_ON_CRITICAL=1
QUALITY_GATE_FAIL_ON_HIGH=10

# Webhook secrets
GITHUB_WEBHOOK_SECRET=
GITLAB_WEBHOOK_TOKEN=
BITBUCKET_WEBHOOK_SECRET=
```

---

*CodeGuardian AI — Every line of code, in every language, held to the highest standard.*
