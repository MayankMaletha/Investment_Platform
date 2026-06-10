"""
main.py — FastAPI application factory and entry point.

Responsibilities:
- Create and configure the FastAPI app instance
- Register all middleware (CORS, GZip, logging)
- Mount all routers under versioned prefixes
- Register global exception handlers
- Manage application lifespan (startup/shutdown hooks)
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.exceptions import RequestValidationError

from config import settings
from core.logging import setup_logging, logger
from core.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)
from database.session import engine, Base
from api.routes import auth, stocks, crypto, portfolio, news, chat, watchlist, risk, rag
from websocket.manager import websocket_router


# ─── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Startup: initialise logging, create DB tables, warm up ML models.
    Shutdown: close DB connections and release resources.
    """
    setup_logging()
    logger.info("Starting AI Investment Agent", version=settings.APP_VERSION, env=settings.ENVIRONMENT)

    # Create tables (idempotent – use Alembic for production migrations)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema ready")

    # Optionally pre-warm FinBERT to avoid cold-start latency on first request
    if settings.ENVIRONMENT != "production":
        try:
            from services.sentiment_service import SentimentService
            SentimentService._load_pipeline()
        except Exception:
            pass

    logger.info("Application startup complete — ready to serve")
    yield

    # Shutdown
    logger.info("Shutting down...")
    try:
        from core import dependencies
        if dependencies._finnhub_client is not None:
            await dependencies._finnhub_client.close()
        if dependencies._finnhub_service is not None and dependencies._finnhub_service.cache is not None:
            await dependencies._finnhub_service.cache.close()
    except Exception as exc:
        logger.warning("Finnhub resources close skipped", error=str(exc))
    await engine.dispose()
    logger.info("Database pool closed")


# ─── App Factory ──────────────────────────────────────────────────────────────

def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-powered investment analysis platform with multi-agent reasoning.",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ── Middleware (order matters — outermost = first to process requests) ────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # ── Exception Handlers ────────────────────────────────────────────────────
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # ── API Routers ───────────────────────────────────────────────────────────
    p = settings.API_V1_PREFIX
    app.include_router(auth.router,      prefix=f"{p}/auth",      tags=["Authentication"])
    app.include_router(stocks.router,    prefix=f"{p}/stocks",    tags=["Stocks"])
    app.include_router(crypto.router,    prefix=f"{p}/crypto",    tags=["Crypto"])
    app.include_router(portfolio.router, prefix=f"{p}/portfolio", tags=["Portfolio"])
    app.include_router(news.router,      prefix=f"{p}/news",      tags=["News"])
    app.include_router(chat.router,      prefix=f"{p}/chat",      tags=["AI Chat"])
    app.include_router(watchlist.router, prefix=f"{p}/watchlist", tags=["Watchlist"])
    app.include_router(risk.router,      prefix=f"{p}/risk",      tags=["Risk"])
    app.include_router(rag.router,       prefix=f"{p}/rag",       tags=["RAG"])
    app.include_router(websocket_router,                           tags=["WebSockets"])

    # ── Health / Readiness ────────────────────────────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health():
        return {"status": "healthy", "version": settings.APP_VERSION, "env": settings.ENVIRONMENT}

    @app.get("/ready", tags=["Health"])
    async def readiness():
        """Check DB connectivity before marking pod as ready."""
        try:
            async with engine.connect() as conn:
                await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            return {"status": "ready"}
        except Exception as e:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=503, content={"status": "not ready", "error": str(e)})

    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else 4,
        log_level=settings.LOG_LEVEL.lower(),
    )
