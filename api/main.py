"""
AssessIQ - Main FastAPI Application
=====================================
AI-Powered Student Answer Evaluation System

This is the main entry point for the FastAPI backend.
It handles all API routes, middleware configuration, and application lifecycle.
"""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Import configuration
from config.settings import settings, setup_directories

# Import routers
from api.routes import upload, evaluation, results

# ========== Logging Configuration ==========
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.LOG_FILE, mode='a')
    ]
)
logger = logging.getLogger("AssessIQ")


# ========== Application Lifecycle ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle application startup and shutdown events.
    - Startup: Initialize directories, load models, connect to database
    - Shutdown: Clean up resources, close connections
    """
    # ===== STARTUP =====
    logger.info("=" * 60)
    logger.info(f"[START] Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("=" * 60)
    
    # Setup directories
    setup_directories()
    logger.info("[OK] Directories initialized")
    
    # NOTE: Models are loaded lazily on first request to reduce startup memory
    # This helps with free-tier hosting (512MB RAM limit)
    logger.info("[INFO] ML models will be loaded on first request (lazy loading)")
    
    logger.info(f"[SERVER] API running at http://{settings.API_HOST}:{settings.API_PORT}")
    logger.info("=" * 60)
    
    yield  # Application is running
    
    # ===== SHUTDOWN =====
    logger.info("[STOP] Shutting down AssessIQ...")
    logger.info("[BYE] Goodbye!")


# ========== FastAPI Application ==========
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# ========== CORS Middleware ==========
# Allow all origins for API access (wildcards don't work in FastAPI CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Must be False when using "*"
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# ========== Request Logging Middleware ==========
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for debugging and monitoring."""
    start_time = datetime.now()
    
    # Process the request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = (datetime.now() - start_time).total_seconds()
    
    # Log the request
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    # Add processing time header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# ========== Exception Handlers ==========
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent JSON response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.status_code,
                "message": exc.detail
            },
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": 500,
                "message": "Internal server error. Please try again later."
            },
            "timestamp": datetime.now().isoformat()
        }
    )


# ========== Include Routers ==========
app.include_router(
    upload.router,
    prefix=f"{settings.API_PREFIX}/upload",
    tags=["Upload"]
)

app.include_router(
    evaluation.router,
    prefix=f"{settings.API_PREFIX}/evaluate",
    tags=["Evaluation"]
)

app.include_router(
    results.router,
    prefix=f"{settings.API_PREFIX}/results",
    tags=["Results"]
)


# ========== Static Files (for uploaded files) ==========
if os.path.exists(settings.UPLOAD_DIR):
    app.mount(
        "/uploads",
        StaticFiles(directory=settings.UPLOAD_DIR),
        name="uploads"
    )


# ========== Root Endpoints ==========
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - Welcome message and API information.
    """
    return {
        "success": True,
        "message": f"Welcome to {settings.APP_NAME}!",
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "endpoints": {
            "upload": f"{settings.API_PREFIX}/upload",
            "evaluate": f"{settings.API_PREFIX}/evaluate",
            "results": f"{settings.API_PREFIX}/results"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/info", tags=["Info"])
async def api_info():
    """
    Get detailed API information and configuration.
    """
    return {
        "success": True,
        "data": {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "ocr_engine": settings.OCR_ENGINE,
            "nlp_model": settings.SPACY_MODEL,
            "semantic_model": settings.SENTENCE_TRANSFORMER_MODEL,
            "scoring_weights": {
                "semantic": settings.WEIGHT_SEMANTIC,
                "keyword": settings.WEIGHT_KEYWORD,
                "diagram": settings.WEIGHT_DIAGRAM
            },
            "thresholds": {
                "excellent": settings.SEMANTIC_EXCELLENT_THRESHOLD,
                "good": settings.SEMANTIC_GOOD_THRESHOLD,
                "average": settings.SEMANTIC_AVERAGE_THRESHOLD
            }
        }
    }


# ========== Run Application ==========
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
