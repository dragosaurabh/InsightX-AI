"""
InsightX AI - Health Check Endpoint

Provides health check endpoint for monitoring and load balancers.
"""

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter

from app.config import get_settings
from app.models.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns service status, version, and component health.
    Used by load balancers and monitoring systems.
    """
    settings = get_settings()
    
    components = {
        "api": "healthy",
        "config": "healthy"
    }
    
    # Check data file
    data_path = Path(settings.data_path)
    if data_path.exists():
        components["data"] = "healthy"
    else:
        components["data"] = "missing"
    
    # Check Redis if configured
    if settings.redis_url:
        components["redis"] = "configured"
    else:
        components["redis"] = "not_configured"
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        components=components
    )
