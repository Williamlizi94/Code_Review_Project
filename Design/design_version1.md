<div align="center">

# 🛡️ CodeGuardian AI — Intelligent Code Review Agent

> A multi-language, context-aware code review platform for enterprises and teams,
> powered by LLM reasoning + static rule engines + RAG augmentation.

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-ReAct_Agent-1C3C3C?style=flat-square&logo=chainlink&logoColor=white)](https://langchain.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--5.4--mini-412991?style=flat-square&logo=openai&logoColor=white)](https://openai.com)
[![Semgrep](https://img.shields.io/badge/Semgrep-30%2B_Languages-20B2AA?style=flat-square)](https://semgrep.dev)
[![pgvector](https://img.shields.io/badge/pgvector-RAG-336791?style=flat-square&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![License](https://img.shields.io/badge/License-Apache%202.0-E25822?style=flat-square)](../LICENSE)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Supported Languages](#-supported-languages)
- [Core Features](#-core-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Module Reference](#-module-reference)
- [API Reference](#-api-reference)
- [Configuration](#-configuration)
- [CI/CD Integration](#-cicd-integration)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)

---

## 📖 Overview

**CodeGuardian AI** is an intelligent code review Agent built for enterprises and development teams. It combines Semgrep's 30+ language static analysis with Tree-sitter AST parsing, LLM reasoning via LangGraph, and RAG-augmented defect retrieval — delivering multi-dimensional, actionable code diagnostics and fix suggestions across any tech stack.

### 💡 Pain Points Addressed

| ❌ Traditional Static Analysis Pain Points | ✅ CodeGuardian AI Solution |
|---|---|
| Fixed rules, high false-positive rate | LLM understands context semantically, filters invalid alerts |
| Cannot understand business logic | RAG retrieves private knowledge base & historical defect cases |
| Language-locked tools, can't cover polyglot repos | Semgrep + Tree-sitter covers 30+ languages in one pipeline |
| Unreadable reports developers ignore | Structured HTML / Markdown / PDF reports with precise Diff location |
| Can only be triggered manually | Webhook + REST API auto-integrates with PR / MR / pipeline |
| Multiple disconnected tools, scattered results | Unified Agent orchestrates all analyzers in a single workflow |

---

## 🌐 Supported Languages

| Language | Static Analysis | AST Parsing | Style Rules |
|---|---|---|---|
| 🐍 Python | Semgrep, Bandit | Tree-sitter | PEP8 / Black |
| ☕ Java | Semgrep | Tree-sitter | Google Java Style |
| 🟦 TypeScript / JavaScript | Semgrep, ESLint | Tree-sitter | Airbnb / Standard |
| 🐹 Go | Semgrep, Staticcheck | Tree-sitter | Effective Go |
| 🦀 Rust | Semgrep, Clippy | Tree-sitter | Rust API Guidelines |
| ⚙️ C / C++ | Semgrep | Tree-sitter | MISRA C / CERT |
| 💎 Ruby | Semgrep, RuboCop | Tree-sitter | Ruby Style Guide |
| 🐘 PHP | Semgrep | Tree-sitter | PSR-12 |
| 🍎 Swift / Kotlin | Semgrep | Tree-sitter | Official Style Guides |

---

## ⚡ Core Features

### 🔍 1. Multi-Scope Review

Five review granularities supported:

- 🏢 **Project-level** — Clone an entire Git repository and run a full scan
- 📁 **Directory-level** — Target a specific module or package path for partial review
- 📄 **File-level** — Upload a single file or specify its path
- 📝 **Code snippet** — Paste a code block for instant review (no repository required)
- ⚡ **Incremental mode** — Based on `git diff`, only review lines changed in the current PR

### ⚙️ 2. Dual-Engine Deep Analysis (AI + Rules)

```
User Code
    │
    ├─► 📏 Rule Engine Layer
    │       ├─► Semgrep       (30+ languages, OWASP / security / style rulesets)
    │       ├─► Tree-sitter   (AST-level structural analysis)
    │       └─► Language-specific linters (ESLint / Bandit / Staticcheck / Clippy ...)
    │               └─► Structured issue list (location + rule ID + severity)
    │
    ├─► 🧠 LLM Reasoning Layer (LangGraph Agent)
    │       ├─► Tool calls to local analyzers
    │       ├─► Semantic understanding & business logic analysis
    │       └─► Fix suggestion generation (before/after code diff)
    │
    └─► 🔎 RAG Augmentation Layer
            ├─► Similar historical defect retrieval (BM25 + vector hybrid search)
            ├─► Rerank for precision
            └─► Inject enriched context into LLM prompt
```

**Analysis Dimensions:**

| Dimension | What's Checked |
|---|---|
| 🎨 Code style | Naming conventions, formatting, comments |
| 🔒 Security | SQL injection, XSS, SSRF, deserialization — OWASP Top 10 |
| ⚡ Performance | N+1 queries, blocking I/O in async context, memory leak risks |
| 🔧 Maintainability | Cyclomatic complexity, duplicate code, magic numbers |
| 💼 Business logic | Potential logic defects inferred via RAG knowledge base |

### 🧠 3. RAG Knowledge Augmentation

- 📂 **Knowledge sources** — Historical review records, internal coding standard documents, defect case libraries
- 🔍 **Retrieval strategy** — BM25 keyword search + vector semantic search hybrid + Cross-Encoder Rerank
- 🌳 **Code-aware chunking** — Tree-sitter splits documents at function/class boundaries, not arbitrary character counts
- 💾 **Storage** — pgvector (vectors) + PostgreSQL FTS (full-text, built-in)
- 🖥️ **Management UI** — Knowledge base upload, categorization, version management

### 🔧 4. LangGraph Tool Orchestration

The LLM Agent drives local analyzers through structured tool calls via a LangGraph ReAct loop, ensuring outputs are trustworthy and verifiable:

```python
# Example tool call emitted by the Agent
{
  "tool": "run_semgrep",
  "args": { "path": "src/", "ruleset": "p/owasp-top-ten", "lang": "python" }
}
```

Built-in tool set:

`run_semgrep` · `run_eslint` · `run_bandit` · `run_staticcheck` · `parse_ast` · `get_git_diff` · `search_knowledge_base`

### 📊 5. Professional Review Reports

- **Formats** — `HTML` (interactive) · `Markdown` · `PDF`
- **Contents**
  - 🗺️ Issue distribution heatmap (by file / by severity / by language)
  - 📈 Severity statistics (Critical / High / Medium / Low / Info)
  - 📍 Precise line-number location + highlighted Diff view
  - 🤖 AI-generated fix suggestions (with before/after code comparison)
  - 📉 Historical trend comparison across review runs

### 📚 6. Review History & Search

- All review tasks persisted in PostgreSQL
- Paginated queries, keyword search, language filter, and status filtering
- Follow-up conversations on historical results (conversational review mode)
- Review results exportable as knowledge base entries

### 📏 7. Coding Standard Management

- 📦 **Built-in standard templates** — Google Style / Airbnb / PEP8 / Effective Go / MISRA C / CERT / OWASP
- ✏️ **Custom standards** — Upload private standard documents; AI automatically parses them into executable rules
- 🔖 **Standard versioning** — Standard updates do not affect the traceability of historical review results

### 🔀 8. Git Integration

- Configure Git platform URL (GitHub / GitLab / Bitbucket) and Access Token
- Automatic Clone / Pull of the latest code
- Incremental analysis: only review the `git diff` change scope to reduce noise
- Review results automatically written back as PR/MR inline comments

### 🔄 9. CI/CD Integration

- 🪝 **Webhook** — Automatically trigger review when a PR/MR is created or updated
- 🔌 **REST API** — Actively call from a pipeline stage to retrieve review reports
- 🚦 **Quality gate** — Block builds based on severity thresholds (e.g., fail if Critical > 0)
- 🔩 **Build plugins** *(planned)* — GitHub Action / pre-commit hook

### 🔒 10. Security & Compliance

- 🙈 Sensitive information redaction (secrets, tokens, passwords never reach the LLM)
- 🔑 Git credentials stored only in the current session (optional encrypted persistence)
- 📋 Full audit log (operator, timestamp, input digest, output digest)
- 🔭 Distributed tracing (trace ID spans the entire pipeline for easy debugging)

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Access Layer                          │
│   Web Browser / UI    Git Webhook    CI/CD Pipeline          │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                   Gateway & Auth Layer                        │
│            FastAPI Router  ·  JWT Bearer Auth                 │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                      Core Service Layer                       │
│                                                              │
│  ┌─────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Review Scheduler│  │  Git Service │  │ Report Service  │  │
│  │  (Celery Tasks) │  │  (GitPython) │  │  (Jinja2/PDF)  │  │
│  └────────┬────────┘  └──────────────┘  └────────────────┘  │
│           │                                                  │
│  ┌────────▼────────────────────────────────────────────┐    │
│  │           LangGraph AI Agent Execution Engine        │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │    │
│  │  │  LLM Client  │  │  Tool Node   │  │  Prompt   │  │    │
│  │  │ (LangChain)  │  │ (Semgrep/AST)│  │  Builder  │  │    │
│  │  └──────────────┘  └──────────────┘  └───────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                     RAG Engine                        │   │
│  │  Knowledge Mgmt  ·  Hybrid Search (pgvector+BM25)  · Rerank│
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                     Data Infrastructure                       │
│                                                              │
│  PostgreSQL + pgvector    Redis              S3 / MinIO       │
│  (metadata + vectors)     (cache / queue)   (file storage)   │
└──────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                        AI Model Layer                         │
│       OpenAI GPT-5.4-mini / GPT-5.5  ·  Ollama (local)       │
└──────────────────────────────────────────────────────────────┘
```

### 🔄 Internal Event Flow (Review Pipeline)

```
ReviewRequest
    │
    ▼
[1] 📥 GitCloneTask       → Clone / pull latest code (GitPython)
    │
    ▼
[2] 🔬 StaticAnalysisTask → Semgrep + language-specific linters run in parallel (Celery)
    │
    ▼
[3] 🌳 ASTParseTask       → Tree-sitter builds AST, extracts function/class context
    │
    ▼
[4] 🧠 RAGRetrievalTask   → Retrieve similar historical defects, build augmented context
    │
    ▼
[5] 🤖 LLMReviewTask      → LangGraph Agent: tool calls + prompt construction + LLM inference
    │
    ▼
[6] 🔀 ResultMergeTask    → Deduplication, severity ranking, structuring
    │
    ▼
[7] 📊 ReportGenerateTask → HTML / Markdown / PDF report (Jinja2 + WeasyPrint)
    │
    ▼
[8] 📣 NotifyTask         → Write back PR comments / Webhook callback / email notification
```

---

## 🛠️ Tech Stack

| Category | Technology |
|---|---|
| **Language** | ![Python](https://img.shields.io/badge/-Python_3.12+-3776AB?style=flat-square&logo=python&logoColor=white) |
| **Web Framework** | ![FastAPI](https://img.shields.io/badge/-FastAPI_+_Uvicorn-009688?style=flat-square&logo=fastapi&logoColor=white) |
| **AI Agent** | ![LangChain](https://img.shields.io/badge/-LangChain_+_LangGraph-1C3C3C?style=flat-square) |
| **LLM** | ![OpenAI](https://img.shields.io/badge/-GPT--5.4--mini_/_GPT--5.5-412991?style=flat-square&logo=openai&logoColor=white) |
| **Static Analysis** | Semgrep · Bandit · ESLint · Staticcheck · Clippy |
| **AST Parsing** | Tree-sitter (universal, language-agnostic) |
| **RAG Retrieval** | LlamaIndex + BM25 + pgvector + Cross-Encoder Rerank |
| **Embedding Models** | `text-embedding-3-small` / `nomic-embed-code` (Ollama) |
| **Task Queue** | ![Celery](https://img.shields.io/badge/-Celery_+_Redis-37814A?style=flat-square&logo=celery&logoColor=white) |
| **Data Storage** | ![PostgreSQL](https://img.shields.io/badge/-PostgreSQL_+_pgvector-336791?style=flat-square&logo=postgresql&logoColor=white) |
| **File Storage** | AWS S3 / MinIO |
| **Document Parsing** | Unstructured.io |
| **Report Generation** | Jinja2 + WeasyPrint |
| **Auth** | FastAPI-Users + JWT |
| **Git Operations** | GitPython · PyGithub · python-gitlab · atlassian-python-api |
| **Build & Deploy** | ![Docker](https://img.shields.io/badge/-Docker_+_Poetry-2496ED?style=flat-square&logo=docker&logoColor=white) |
| **Monitoring** | Loguru · OpenTelemetry · Grafana / Loki |
| **Testing** | pytest · pytest-asyncio · Testcontainers |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Poetry (`pip install poetry`)

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/codeguardian-ai.git
cd codeguardian-ai
```

### 2. Start Infrastructure

```bash
# Start PostgreSQL (with pgvector), Redis, and MinIO
docker compose -f docker/compose-dev.yml up -d
```

### 3. Install Dependencies

```bash
poetry install
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
# LLM
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.4-mini

# Database
DATABASE_URL=postgresql+asyncpg://codeguardian:codeguardian@localhost:5432/codeguardian

# Redis
REDIS_URL=redis://localhost:6379/0

# File Storage
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=codeguardian

# Auth
JWT_SECRET=change-me-in-production
```

### 5. Initialize the Database

```bash
poetry run alembic upgrade head
```

### 6. Run the Application

```bash
# Terminal 1: API server
poetry run uvicorn app.main:app --reload --port 8080

# Terminal 2: Celery worker (async analysis tasks)
poetry run celery -A app.worker worker --loglevel=info
```

### 7. Open the Web UI

Navigate to [http://localhost:8080](http://localhost:8080)

> Default credentials: `admin / codeguardian123`

---

## 📁 Module Reference

```
codeguardian-ai/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── agent/                  # 🤖 LangGraph AI Agent
│   │   ├── graph.py            # Agent graph definition (ReAct loop)
│   │   ├── tools/              # Tool node definitions
│   │   │   ├── semgrep.py      # Semgrep wrapper
│   │   │   ├── tree_sitter.py  # AST parser wrapper
│   │   │   ├── linters.py      # Language-specific linter wrappers
│   │   │   └── git_diff.py     # Git diff extractor
│   │   └── prompts/            # Prompt templates (Jinja2)
│   ├── review/                 # 🔍 Review business core
│   │   ├── service.py          # Review task entry point
│   │   ├── pipeline/           # Pipeline stage implementations
│   │   └── merger.py           # Result deduplication & ranking
│   ├── analyzer/               # 🔬 Static analyzer wrappers
│   │   ├── semgrep.py
│   │   ├── bandit.py           # Python security
│   │   ├── eslint.py           # JS/TS
│   │   └── staticcheck.py      # Go
│   ├── rag/                    # 🧠 RAG engine
│   │   ├── knowledge.py        # Knowledge base management
│   │   ├── hybrid_search.py    # BM25 + vector hybrid search
│   │   └── rerank.py           # Cross-Encoder reranker
│   ├── git/                    # 🔀 Git operations
│   │   └── service.py          # Clone, pull, diff (GitPython)
│   ├── report/                 # 📊 Report generation
│   │   ├── html.py             # Jinja2 HTML report
│   │   ├── markdown.py
│   │   └── pdf.py              # WeasyPrint PDF
│   ├── webhook/                # 🪝 Webhook receiver & event routing
│   │   ├── github.py
│   │   ├── gitlab.py
│   │   └── bitbucket.py
│   ├── auth/                   # 🔒 JWT auth (FastAPI-Users)
│   ├── models/                 # 💾 SQLAlchemy ORM models
│   ├── schemas/                # 📐 Pydantic request/response schemas
│   ├── worker.py               # ⚙️ Celery app & task definitions
│   └── config.py               # 🔧 Settings (pydantic-settings)
├── docker/
│   ├── compose-dev.yml         # Development infrastructure
│   └── compose-prod.yml        # Full production deployment
├── migrations/                 # Alembic database migrations
├── tests/                      # pytest test suite
│   ├── unit/
│   └── integration/
├── docs/
│   ├── api.md
│   └── architecture.md
├── pyproject.toml
└── .env.example
```

---

## 🔌 API Reference

### Submit a Review Task

```http
POST /api/v1/reviews
Content-Type: application/json
Authorization: Bearer <token>

{
  "type": "GIT_REPO",           // GIT_REPO | DIRECTORY | FILE | SNIPPET
  "target": "https://github.com/org/repo.git",
  "branch": "feature/login",
  "languages": ["python", "typescript"],   // omit to auto-detect
  "mode": "INCREMENTAL",        // FULL | INCREMENTAL
  "rulesetId": "owasp-top-ten",
  "notifyWebhook": "https://your-ci/callback"
}
```

### Fetch Review Results

```http
GET /api/v1/reviews/{reviewId}
GET /api/v1/reviews/{reviewId}/report?format=html
```

### List Review History

```http
GET /api/v1/reviews?page=0&size=20&keyword=injection&severity=HIGH&lang=python
```

### Knowledge Base Management

```http
POST /api/v1/knowledge/upload     # Upload a standard document
GET  /api/v1/knowledge/search     # Search for similar cases
```

### Webhooks

```http
POST /api/v1/webhook/github
POST /api/v1/webhook/gitlab
POST /api/v1/webhook/bitbucket
```

> Full API docs: [docs/api.md](../docs/api.md) · `/docs` Swagger UI after startup

---

## ⚙️ Configuration

### Switching AI Models

```env
OPENAI_MODEL=gpt-5.4-mini       # default — cost-efficient
# OPENAI_MODEL=gpt-5.5          # max quality
# OLLAMA_MODEL=codellama:34b    # local, air-gapped deployments
```

### Enabling / Disabling Analyzers

```env
ANALYZER_SEMGREP_ENABLED=true
ANALYZER_BANDIT_ENABLED=true       # Python only
ANALYZER_ESLINT_ENABLED=true       # JS/TS only
ANALYZER_STATICCHECK_ENABLED=true  # Go only
ANALYZER_CLIPPY_ENABLED=true       # Rust only
```

### Semgrep Rulesets

```env
SEMGREP_RULES=p/owasp-top-ten,p/secrets,p/python,p/typescript
```

### 🚦 Quality Gate Thresholds

```env
QUALITY_GATE_ENABLED=true
QUALITY_GATE_FAIL_ON_CRITICAL=1    # Fail if Critical issues >= 1
QUALITY_GATE_FAIL_ON_HIGH=10
```

---

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
- name: CodeGuardian AI Review
  uses: your-org/codeguardian-action@v1
  with:
    server-url: ${{ secrets.CODEGUARDIAN_URL }}
    api-token: ${{ secrets.CODEGUARDIAN_TOKEN }}
    fail-on-critical: true
```

### GitLab CI

```yaml
code-review:
  stage: test
  script:
    - |
      RESULT=$(curl -sf -X POST "$CODEGUARDIAN_URL/api/v1/reviews" \
        -H "Authorization: Bearer $CODEGUARDIAN_TOKEN" \
        -d "{\"type\":\"DIRECTORY\",\"target\":\"$CI_PROJECT_DIR\"}" | jq -r '.status')
      [ "$RESULT" = "PASS" ] || exit 1
```

### Jenkins

```groovy
stage('AI Code Review') {
    steps {
        codeguardianReview(
            serverUrl: env.CODEGUARDIAN_URL,
            apiToken: credentials('codeguardian-token'),
            failOnCritical: true
        )
    }
}
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/your-org/codeguardian-ai
    rev: v0.3.0
    hooks:
      - id: codeguardian-review
        args: [--mode, snippet, --fail-on, HIGH]
```

---

## 🗺️ Roadmap

### v0.1 — MVP (Current)
- [x] Project skeleton (FastAPI + Python 3.12)
- [x] Basic REST API design
- [ ] Semgrep integration (multi-language static analysis)
- [ ] LangGraph Agent + OpenAI GPT-5.4-mini review core
- [ ] Basic HTML report generation (Jinja2)
- [ ] PostgreSQL task persistence (SQLAlchemy + Alembic)

### v0.2 — RAG Augmentation
- [ ] pgvector integration + OpenAI embedding models
- [ ] Knowledge base management UI
- [ ] BM25 + vector hybrid retrieval (LlamaIndex)
- [ ] Cross-Encoder Rerank

### v0.3 — Git & CI Integration
- [ ] GitHub / GitLab / Bitbucket Webhook receiver
- [ ] Write review results back as PR/MR inline comments
- [ ] Incremental Diff analysis mode
- [ ] GitHub Actions integration
- [ ] Pre-commit hook support

### v0.4 — Multi-Language Expansion
- [ ] Tree-sitter AST-level analysis for all supported languages
- [ ] ESLint / Bandit / Staticcheck / Clippy / RuboCop integration
- [ ] Language auto-detection
- [ ] Per-language ruleset configuration

### v0.5 — Enterprise Features
- [ ] Multi-tenant support
- [ ] Custom standard document parsing (Unstructured.io)
- [ ] Ollama local model support (air-gapped deployment)
- [ ] PDF report export (WeasyPrint)
- [ ] Full audit logging + OpenTelemetry tracing

### v1.0 — Production Ready
- [ ] Performance load testing & tuning (Celery worker scaling)
- [ ] One-command production deployment via Docker Compose
- [ ] Monitoring dashboard (Grafana + Loki)
- [ ] Full test coverage (≥ 80%)

---

## 🤝 Contributing

1. Fork this repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Install dev dependencies: `poetry install --with dev`
4. Ensure all tests pass: `poetry run pytest`
5. Ensure linting passes: `poetry run ruff check . && poetry run mypy app/`
6. Open a Pull Request describing the purpose of your changes and your test plan

---

## 📄 License

This project is licensed under the [Apache License 2.0](../LICENSE).

---

<div align="center">
<sub>🛡️ <strong>CodeGuardian AI</strong> — Every line of code, in every language, held to the highest standard.</sub>
</div>
