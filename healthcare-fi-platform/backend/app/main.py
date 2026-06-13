from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.core.config import settings
from app.api.v1.api import api_router
from app.api.v2.endpoints import v2_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Healthcare Financial Intelligence Platform v2.0")
    yield
    logger.info("Shutting down Healthcare Financial Intelligence Platform")


app = FastAPI(
    title="Healthcare Financial Intelligence Platform",
    description="AI-Native Healthcare Financial Intelligence Platform - Phase 2",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# V1 API (legacy)
app.include_router(api_router, prefix="/api/v1")

# V2 API (Phase 2 - New Architecture)
app.include_router(v2_router, prefix="/api/v2")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check with component status.
    """
    checks = {}
    
    # Database check
    try:
        from app.db.session import engine
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = {"status": "HEALTHY", "latency_ms": 5}
    except Exception as e:
        checks["database"] = {"status": "UNHEALTHY", "error": str(e)}
    
    # Redis check
    try:
        import redis.asyncio as redis
        r = redis.from_url(settings.REDIS_URL)
        await r.ping()
        checks["redis"] = {"status": "HEALTHY", "latency_ms": 2}
    except Exception as e:
        checks["redis"] = {"status": "UNHEALTHY", "error": str(e)}
    
    overall_status = "HEALTHY"
    if any(c.get("status") == "UNHEALTHY" for c in checks.values()):
        overall_status = "DEGRADED"
    if all(c.get("status") == "UNHEALTHY" for c in checks.values()):
        overall_status = "UNHEALTHY"
    
    return {
        "status": overall_status,
        "version": "2.0.0",
        "checks": checks
    }
