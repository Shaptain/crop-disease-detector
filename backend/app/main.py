"""
app/main.py

Entry point for the Crop Disease Detection API.
Run with: uvicorn app.main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import predict
from app.services import model_service

# ---------------------------------------------------------------------------
# Logging — configure once here; all modules use logging.getLogger(__name__)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown hooks (replaces deprecated @app.on_event)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Crop Disease Detection API...")
    logger.info("Model loaded: %s", model_service.is_model_loaded())
    yield
    # Shutdown
    logger.info("Shutting down Crop Disease Detection API.")


# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Crop Disease Detection API",
    description=(
        "Upload a plant leaf image and receive a disease diagnosis, "
        "confidence score, symptom description, and cure recommendation."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# CORS — allow the Vite dev server during development.
# Add your production domain to the list before deploying.
# ---------------------------------------------------------------------------
ALLOWED_ORIGINS = [
    "http://localhost:5173",    # Vite dev server
    "http://127.0.0.1:5173",   # alternate loopback
    # "https://your-production-domain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(predict.router, prefix="/api/v1", tags=["Prediction"])


# ---------------------------------------------------------------------------
# Root + Health endpoints
# ---------------------------------------------------------------------------
@app.get("/", tags=["Health"], summary="Welcome / API status")
async def root() -> dict:
    """Confirm the API is reachable and point to the docs."""
    return {
        "status": "ok",
        "message": "Crop Disease Detection API is running.",
        "docs": "/docs",
        "model_loaded": model_service.is_model_loaded(),
    }


@app.get("/health", tags=["Health"], summary="Liveness probe")
async def health_check() -> dict:
    """
    Lightweight liveness probe for Docker / Kubernetes health checks.
    Does not trigger any ML workload.
    """
    return {
        "status": "healthy",
        "model_loaded": model_service.is_model_loaded(),
    }