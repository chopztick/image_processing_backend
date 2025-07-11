"""
Health check API endpoints.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.config import settings
from app.schemas.image import HealthResponse, ErrorResponse
from app.services.vector_service import VectorService

router = APIRouter()


@router.get(
    "/",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of the service and its dependencies",
    responses={
        200: {"description": "Service is healthy"},
        503: {"model": ErrorResponse, "description": "Service is unhealthy"},
    },
)
async def health_check(
    session: AsyncSession = Depends(get_async_session),
) -> HealthResponse:
    """
    Perform a comprehensive health check of the service.
    
    Checks:
    - Database connectivity
    - pgvector extension availability
    - Basic service functionality
    
    Returns:
        HealthResponse with status information
    """
    database_connected = False
    pgvector_available = False
    
    try:
        # Test database connectivity
        await session.execute(text("SELECT 1"))
        database_connected = True
        
        # Test pgvector extension
        result = await session.execute(
            text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
        )
        pgvector_available = result.scalar()
        
        # Test vector operations if pgvector is available
        if pgvector_available:
            # Test basic vector operation
            await session.execute(
                text("SELECT '[1,2,3]'::vector <-> '[1,2,4]'::vector")
            )
        
    except Exception:
        # If any test fails, continue to return status
        pass
    
    # Determine overall health status
    is_healthy = database_connected and pgvector_available
    
    health_response = HealthResponse(
        status="healthy" if is_healthy else "unhealthy",
        database_connected=database_connected,
        pgvector_available=pgvector_available,
        timestamp=datetime.utcnow(),
        version=settings.VERSION,
    )
    
    if not is_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_response.dict(),
        )
    
    return health_response


@router.get(
    "/detailed",
    response_model=dict,
    summary="Detailed health check",
    description="Get detailed health information including database statistics",
    responses={
        200: {"description": "Detailed health information"},
        503: {"model": ErrorResponse, "description": "Service is unhealthy"},
    },
)
async def detailed_health_check(
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get detailed health information including database statistics.
    
    Returns comprehensive information about:
    - Service status
    - Database connectivity and statistics
    - pgvector extension status
    - Embedding statistics
    - Configuration information
    """
    try:
        # Basic health check
        basic_health = await health_check(session)
        
        # Get embedding statistics
        embedding_stats = await VectorService.get_embedding_stats(session)
        
        # Get database version
        db_version_result = await session.execute(text("SELECT version()"))
        db_version = db_version_result.scalar()
        
        # Get pgvector version if available
        pgvector_version = None
        if basic_health.pgvector_available:
            try:
                pgvector_version_result = await session.execute(
                    text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
                )
                pgvector_version = pgvector_version_result.scalar()
            except Exception:
                pgvector_version = "unknown"
        
        return {
            "service": {
                "name": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "status": basic_health.status,
                "timestamp": basic_health.timestamp,
            },
            "database": {
                "connected": basic_health.database_connected,
                "version": db_version,
            },
            "pgvector": {
                "available": basic_health.pgvector_available,
                "version": pgvector_version,
            },
            "embeddings": embedding_stats,
            "configuration": {
                "embedding_dimension": settings.EMBEDDING_DIMENSION,
                "max_file_size": settings.MAX_FILE_SIZE,
                "allowed_extensions": settings.ALLOWED_EXTENSIONS,
                "similarity_threshold": settings.SIMILARITY_THRESHOLD,
                "max_similar_results": settings.MAX_SIMILAR_RESULTS,
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to perform detailed health check: {str(e)}",
        )


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description="Check if the service is ready to handle requests",
    responses={
        200: {"description": "Service is ready"},
        503: {"description": "Service is not ready"},
    },
)
async def readiness_check(
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Check if the service is ready to handle requests.
    
    This is a lightweight check that verifies essential dependencies
    are available for the service to function properly.
    """
    try:
        # Test database connectivity
        await session.execute(text("SELECT 1"))
        
        # Test pgvector extension
        result = await session.execute(
            text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
        )
        pgvector_available = result.scalar()
        
        if not pgvector_available:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="pgvector extension is not available",
            )
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service is not ready: {str(e)}",
        )


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness check",
    description="Check if the service is alive",
    responses={
        200: {"description": "Service is alive"},
    },
)
async def liveness_check() -> dict:
    """
    Check if the service is alive.
    
    This is a minimal check that only verifies the service is running
    and can respond to requests. It doesn't check dependencies.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow(),
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }