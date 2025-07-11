"""
Main FastAPI application for the Image Processing Service.
"""

from contextlib import asynccontextmanager
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api import api_router
from app.core.config import settings
from app.core.database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="A cloud-native backend service for image processing with vector-based similarity search",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "The request contains invalid data",
            "details": exc.errors(),
        },
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Handle database errors.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database Error",
            "message": "A database error occurred",
            "details": str(exc) if settings.DEBUG else "Internal server error",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle general exceptions.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "details": str(exc) if settings.DEBUG else "Internal server error",
        },
    )


@app.get("/", include_in_schema=False)
async def root() -> Dict[str, Any]:
    """
    Root endpoint with service information.
    """
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": f"{settings.API_V1_STR}/health",
        "api": f"{settings.API_V1_STR}",
    }


@app.get("/info", include_in_schema=False)
async def info() -> Dict[str, Any]:
    """
    Service information endpoint.
    """
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": "Image Processing Service with Vector Similarity Search",
        "features": [
            "Image upload and validation",
            "Mock embedding generation",
            "Vector similarity search using pgvector",
            "RESTful API with OpenAPI documentation",
            "Async processing with FastAPI",
            "PostgreSQL with pgvector integration",
        ],
        "endpoints": {
            "upload": f"{settings.API_V1_STR}/images/upload",
            "list": f"{settings.API_V1_STR}/images/",
            "get": f"{settings.API_V1_STR}/images/{{image_id}}",
            "similar": f"{settings.API_V1_STR}/images/{{image_id}}/similar",
            "health": f"{settings.API_V1_STR}/health",
        },
        "configuration": {
            "max_file_size": settings.MAX_FILE_SIZE,
            "allowed_extensions": settings.ALLOWED_EXTENSIONS,
            "embedding_dimension": settings.EMBEDDING_DIMENSION,
            "similarity_threshold": settings.SIMILARITY_THRESHOLD,
        },
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )