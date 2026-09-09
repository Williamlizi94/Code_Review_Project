<div align="center">

# 🛡️ CodeGuardian AI

### AI-powered security reviews for repositories and code snippets

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-Apache--2.0-E25822?style=flat-square)](LICENSE)

[Open the live app](https://reviewcodeai.com/) · [Sign in](https://reviewcodeai.com/01-login.html) · [API documentation](https://reviewcodeai.com/docs)

</div>

---

CodeGuardian AI combines static analysis and LLM-assisted reasoning to help teams find security, reliability, and maintainability issues before code is merged.

## Live demo

The production app is available at **[reviewcodeai.com](https://reviewcodeai.com/)**.

| Link | Purpose |
|---|---|
| [Product UI](https://reviewcodeai.com/) | Browse the web interface |
| [Login / Sign up](https://reviewcodeai.com/01-login.html) | Create an account or continue with Google |
| [Swagger API docs](https://reviewcodeai.com/docs) | Explore and test the REST API |
| [Health check](https://reviewcodeai.com/health) | Confirm the production API is online |

## What it does

- Reviews raw code snippets, files, directories, and Git repositories.
- Runs Semgrep, Bandit, Tree-sitter, and language-specific analyzers.
- Uses a configurable LLM provider (Groq, OpenAI, or Ollama) to add context and fix suggestions.
- Runs reviews asynchronously through Celery and Redis.
- Creates HTML, Markdown, and PDF reports.
- Supports GitHub, GitLab, Bitbucket webhooks and configurable quality gates.
- Provides email/password authentication plus Google sign-in.

## Quick start

### 1. Configure your environment

```bash
cp .env.example .env
```

Set at least `GROQ_API_KEY` (or configure another supported LLM provider). Never commit `.env`, `.env.production`, OAuth client JSON files, or private keys.

### 2. Start local infrastructure

```bash
docker compose -f docker/compose-dev.yml up -d
```

### 3. Install dependencies and run the API

```bash
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload --port 8080
```

In another terminal, start the review worker:

```bash
poetry run celery -A app.worker worker --loglevel=info
```

Open `http://localhost:8080/docs` to use the API locally.

## Submit a review

After logging in, submit a `SNIPPET` review with a Bearer token:

```bash
curl -X POST http://localhost:8080/api/v1/reviews \
  -H "Authorization: Bearer <access-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "SNIPPET",
    "mode": "FULL",
    "snippet_language": "python",
    "snippet_content": "query = \"SELECT * FROM users WHERE id = \" + user_id"
  }'
```

The API returns a review ID immediately. Poll `GET /api/v1/reviews/{review_id}` until the status is `COMPLETED`.

## Architecture

```text
Web UI / REST client
        │
        ▼
FastAPI API ──► PostgreSQL + pgvector
        │                 │
        ▼                 ▼
Celery + Redis      MinIO / S3 storage
        │
        ▼
Static analyzers + LLM review pipeline
```

## Production deployment

The production stack is Docker-based and served through Caddy with automatic HTTPS:

```bash
docker compose --env-file .env -f docker/compose-prod.yml up -d --build
```

Production configuration belongs in a private `.env` file on the server. The repository intentionally ignores environment files, OAuth secrets, deployment credentials, and logs.

## Project layout

```text
app/          FastAPI routes, review pipeline, analyzers, workers
frontend/     Static product UI
docker/       Development and production Compose configuration
migrations/   Alembic database migrations
tests/        Unit and integration tests
Design/       Product and architecture documents
```

## Documentation

- [Architecture and feature specification](Design/design_version1.md)
- [架构与功能设计文档（中文）](Design/design_version1_cn.md)

## License

[Apache License 2.0](LICENSE)
