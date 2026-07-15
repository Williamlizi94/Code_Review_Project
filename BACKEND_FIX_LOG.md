# Backend Fix Log

## 2026-07-15

Technical changes:
- Fixed SQLAlchemy Declarative startup failure by renaming ORM attributes that used the reserved `metadata` name to `extra_metadata` while preserving the existing database column name where applicable.
- Scoped review detail and report queries to the authenticated owner, with superuser bypass support, to prevent cross-user review/report reads.
- Scoped knowledge document listing, API hybrid search, and review-pipeline RAG retrieval to the authenticated owner, with superuser bypass support where applicable.
- Parameterized pgvector SQL in hybrid search and document ingestion to avoid direct string interpolation of user-controlled filters and vector values.
- Added non-blocking Celery enqueue handling: enqueue failures are logged, best-effort status updates mark reviews as `FAILED`, and unavailable Redis/PostgreSQL infrastructure no longer breaks API responses.
- Added missing dependencies: `email-validator` for Pydantic `EmailStr`, `aiosqlite` for SQLite async tests, and `bcrypt <4.1` for passlib compatibility.
- Added `.gitignore` entries for local virtual environments, Python bytecode, pytest cache, coverage files, and `.env`.

Verification:
- Run command: `.\.venv-win\Scripts\python.exe -m pytest -q`
- Result: `17 passed, 1 warning in 9.51s`
