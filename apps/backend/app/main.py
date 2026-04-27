"""
LMS Backend - Main Application Entry Point
"""
from contextlib import asynccontextmanager
import logging
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.router import api_router


setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Starting %s...", settings.PROJECT_NAME)
    
    # Ensure storage directory exists
    storage_path = Path(settings.STORAGE_PATH)
    storage_path.mkdir(parents=True, exist_ok=True)
    
    yield
    # Shutdown
    logger.info("Shutting down %s...", settings.PROJECT_NAME)


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Learning Management System API",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


@app.middleware("http")
async def log_request_and_backend_changes(request: Request, call_next):
    """Log request lifecycle and all backend write operations."""
    method = request.method.upper()
    path = request.url.path
    query = request.url.query
    client_host = request.client.host if request.client else "unknown"
    started = perf_counter()

    logger.debug(
        "[Debug] Request started method=%s path=%s query=%s client=%s",
        method,
        path,
        query,
        client_host,
    )

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (perf_counter() - started) * 1000
        logger.exception(
            "[Error] Request failed method=%s path=%s query=%s client=%s duration_ms=%.2f",
            method,
            path,
            query,
            client_host,
            duration_ms,
        )
        raise

    duration_ms = (perf_counter() - started) * 1000
    status_code = response.status_code

    if method in {"POST", "PUT", "PATCH", "DELETE"}:
        if status_code < status.HTTP_400_BAD_REQUEST:
            logger.info(
                "[Success] Backend change method=%s path=%s status=%s duration_ms=%.2f",
                method,
                path,
                status_code,
                duration_ms,
            )
        else:
            logger.error(
                "[Error] Backend Change failed method=%s path=%s status=%s duration_ms=%.2f",
                method,
                path,
                status_code,
                duration_ms,
            )
    else:
        logger.debug(
            "[Debug] Response completed method=%s path=%s status=%s duration_ms=%.2f",
            method,
            path,
            status_code,
            duration_ms,
        )

    return response

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploaded content
storage_path = Path(settings.STORAGE_PATH)
storage_path.mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=str(storage_path)), name="storage")

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "LMS Backend Running",
        "version": settings.VERSION,
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    """Health check endpoint for Docker/Kubernetes."""
    return {"status": "healthy"}
