"""Health check endpoint for Hydra."""

from fastapi import APIRouter
from app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def get_health():
    """System health and liveness check."""
    return {"status": "ok", "version": settings.VERSION}

