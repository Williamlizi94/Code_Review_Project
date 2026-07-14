from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────
    app_env: Literal["development", "production", "testing"] = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8080
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:8080"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ── Database ─────────────────────────────────────────────────────
    database_url: str = (
        "postgresql+asyncpg://codeguardian:codeguardian@localhost:5432/codeguardian"
    )

    # ── Redis ────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Celery ───────────────────────────────────────────────────────
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # ── LLM ──────────────────────────────────────────────────────────
    openai_api_key: str = ""
    openai_model: str = "gpt-5.4-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    ollama_base_url: str = ""
    ollama_model: str = ""

    # ── File Storage (S3 / MinIO) ─────────────────────────────────────
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "codeguardian"
    s3_region: str = "us-east-1"

    # ── Auth (JWT) ───────────────────────────────────────────────────
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours

    # ── Analyzers ────────────────────────────────────────────────────
    analyzer_semgrep_enabled: bool = True
    analyzer_bandit_enabled: bool = True
    analyzer_eslint_enabled: bool = True
    analyzer_staticcheck_enabled: bool = True
    analyzer_clippy_enabled: bool = False

    semgrep_rules: str = "p/owasp-top-ten,p/secrets,p/python,p/typescript"

    @property
    def semgrep_rules_list(self) -> list[str]:
        return [r.strip() for r in self.semgrep_rules.split(",") if r.strip()]

    # ── Quality Gate ─────────────────────────────────────────────────
    quality_gate_enabled: bool = False
    quality_gate_fail_on_critical: int = 1
    quality_gate_fail_on_high: int = 10

    # ── Git Platform Webhooks ─────────────────────────────────────────
    github_webhook_secret: str = ""
    gitlab_webhook_token: str = ""
    bitbucket_webhook_secret: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
