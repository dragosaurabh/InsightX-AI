"""
InsightX AI - FastAPI Application

Main entry point for the InsightX AI backend API.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import get_settings, validate_settings
from app.api import chat, health
from app.services.analysis_service import get_analysis_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting InsightX AI...")
    
    try:
        validate_settings()
        settings = get_settings()
        
        # Pre-load dataset
        logger.info(f"Loading dataset from {settings.data_path}...")
        try:
            analysis_service = get_analysis_service(settings.data_path)
            logger.info("✓ Dataset loaded successfully")
        except FileNotFoundError:
            logger.warning(f"Dataset not found at {settings.data_path}. API will work but analysis will fail.")
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
        
        logger.info("✓ InsightX AI started successfully")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down InsightX AI...")
    from app.services.llm_service import get_llm_service
    llm = get_llm_service()
    await llm.close()
    logger.info("✓ InsightX AI shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="InsightX AI API",
    description="""
    **InsightX AI** — Conversational analytics for digital payments.
    
    Ask plain English questions, get precise, explainable answers backed by
    deterministic data analysis.
    
    ## Features
    
    - **Natural Language Queries**: Ask questions in plain English
    - **Intent Extraction**: Powered by Gemini for accurate understanding
    - **Deterministic Analysis**: DuckDB-backed for fast, accurate computations
    - **Explainability**: Every response includes the SQL used and method explanation
    - **Session Context**: Maintains conversation history for follow-ups
    
    ## Example Queries
    
    - "What is the overall failure rate in the last 30 days?"
    - "Compare failure rate on Android vs iOS"
    - "Show average transaction amount by category"
    - "Why did failures spike last week?"
    """,
    version="1.0.0",
    contact={
        "name": "InsightX AI Team",
    },
    license_info={
        "name": "MIT",
    },
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
settings = get_settings()
origins = [
    settings.frontend_origin,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API info."""
    return {
        "name": "InsightX AI API",
        "version": "1.0.0",
        "description": "Conversational analytics for digital payments",
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
