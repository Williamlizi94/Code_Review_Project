"""FastAPI application entry point."""

import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.config import get_settings

settings = get_settings()


# ── Logging setup ─────────────────────────────────────────────────────────────

def _setup_logging() -> None:
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
            "<level>{message}</level>"
        ),
        colorize=True,
    )


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    _setup_logging()
    logger.info("CodeGuardian AI starting up")

    # Ensure pgvector extension and DB tables exist
    try:
        from app.database import engine
        from app.models.base import Base
        # Import all models to register them with the metadata
        import app.models.user  # noqa: F401
        import app.models.review  # noqa: F401
        import app.models.knowledge  # noqa: F401
        import app.models.audit  # noqa: F401
    except Exception as exc:
        logger.warning(f"DB warm-up skipped: {exc}")

    logger.info(f"API listening on {settings.app_host}:{settings.app_port}")
    yield
    logger.info("CodeGuardian AI shutting down")


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="CodeGuardian AI",
        description=(
            "Intelligent Code Review Agent — multi-language, context-aware, "
            "powered by LLM + static analysis + RAG."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ──────────────────────────────────────────────────────
    from app.routers.auth import router as auth_router
    from app.routers.knowledge import router as knowledge_router
    from app.routers.reviews import router as reviews_router
    from app.routers.webhooks import router as webhooks_router

    app.include_router(auth_router)
    app.include_router(reviews_router)
    app.include_router(knowledge_router)
    app.include_router(webhooks_router)

    # ── Global exception handler ──────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"Unhandled error on {request.method} {request.url}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    # ── Health check ──────────────────────────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
        return {"status": "ok", "service": "CodeGuardian AI"}

    return app


app = create_app()
