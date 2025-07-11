"""
API package for the Image Processing Service.
"""

from fastapi import APIRouter

from app.api.v1 import images, health

api_router = APIRouter()
api_router.include_router(images.router, prefix="/images", tags=["images"])
api_router.include_router(health.router, prefix="/health", tags=["health"])

__all__ = ["api_router"]