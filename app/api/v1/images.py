"""
Image API endpoints for upload, retrieval, and similarity search.
"""

from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.image import Image
from app.schemas.image import (
    ImageUploadResponse,
    ImageMetadata,
    SimilarImagesResponse,
    ErrorResponse,
)
from app.services.image_processing import ImageProcessingService
from app.services.vector_service import VectorService

router = APIRouter()


@router.post(
    "/upload",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image",
    description="Upload an image file and generate embeddings for similarity search",
    responses={
        201: {"description": "Image uploaded successfully"},
        400: {"model": ErrorResponse, "description": "Invalid file or validation error"},
        413: {"model": ErrorResponse, "description": "File too large"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def upload_image(
    file: UploadFile = File(..., description="Image file to upload"),
    session: AsyncSession = Depends(get_async_session),
) -> ImageUploadResponse:
    """
    Upload an image file and process it for similarity search.
    
    This endpoint:
    1. Validates the uploaded file
    2. Generates a mock embedding vector
    3. Stores the image metadata and embedding in the database
    4. Returns the image ID and processing status
    """
    try:
        # Read file content
        content = await file.read()
        
        # Process the image
        embedding, metadata = await ImageProcessingService.process_image(
            content=content,
            filename=file.filename or "unknown",
            content_type=file.content_type or "application/octet-stream",
        )
        
        # Create image record
        image = Image(
            filename=file.filename or "unknown",
            original_filename=file.filename or "unknown",
            content_type=file.content_type or "application/octet-stream",
            file_size=len(content),
            embedding_vector=embedding,
            image_metadata=metadata,
            processing_status="completed",
            processed_timestamp=datetime.utcnow(),
        )
        
        # Save to database
        session.add(image)
        await session.commit()
        await session.refresh(image)
        
        return ImageUploadResponse(
            id=image.id,
            filename=image.filename,
            message="Image uploaded and processed successfully",
            processing_status=image.processing_status,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image: {str(e)}",
        )


@router.get(
    "/{image_id}",
    response_model=ImageMetadata,
    summary="Get image metadata",
    description="Retrieve metadata for a specific image",
    responses={
        200: {"description": "Image metadata retrieved successfully"},
        404: {"model": ErrorResponse, "description": "Image not found"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def get_image_metadata(
    image_id: UUID,
    session: AsyncSession = Depends(get_async_session),
) -> ImageMetadata:
    """
    Get metadata for a specific image.
    
    Returns detailed information about the image including:
    - File information (name, size, type)
    - Upload and processing timestamps
    - Processing status
    - Additional metadata
    """
    try:
        stmt = select(Image).where(Image.id == image_id)
        result = await session.execute(stmt)
        image = result.scalar_one_or_none()
        
        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found",
            )
        
        return ImageMetadata(
            id=image.id,
            filename=image.filename,
            content_type=image.content_type,
            file_size=image.file_size,
            upload_timestamp=image.upload_timestamp,
            processed_timestamp=image.processed_timestamp,
            processing_status=image.processing_status,
            metadata=image.image_metadata,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve image metadata: {str(e)}",
        )


@router.get(
    "/{image_id}/similar",
    response_model=SimilarImagesResponse,
    summary="Find similar images",
    description="Find images similar to the specified image using vector similarity",
    responses={
        200: {"description": "Similar images found successfully"},
        404: {"model": ErrorResponse, "description": "Image not found"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def find_similar_images(
    image_id: UUID,
    limit: int = 10,
    threshold: float = 0.7,
    session: AsyncSession = Depends(get_async_session),
) -> SimilarImagesResponse:
    """
    Find images similar to the specified image.
    
    Uses pgvector cosine similarity to find images with similar embeddings.
    
    Args:
        image_id: ID of the query image
        limit: Maximum number of similar images to return (default: 10)
        threshold: Minimum similarity threshold (0-1, default: 0.7)
    
    Returns:
        List of similar images with similarity scores
    """
    try:
        # Get the query image embedding
        query_embedding = await VectorService.get_image_embedding(
            session=session,
            image_id=image_id,
        )
        
        if not query_embedding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found or not processed",
            )
        
        # Find similar images
        similar_images = await VectorService.find_similar_images(
            session=session,
            query_embedding=query_embedding,
            query_image_id=image_id,
            limit=limit,
            threshold=threshold,
        )
        
        return SimilarImagesResponse(
            query_image_id=image_id,
            similar_images=similar_images,
            total_results=len(similar_images),
            search_timestamp=datetime.utcnow(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find similar images: {str(e)}",
        )


@router.get(
    "/",
    response_model=List[ImageMetadata],
    summary="List all images",
    description="Get a list of all uploaded images with their metadata",
    responses={
        200: {"description": "Images retrieved successfully"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def list_images(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_async_session),
) -> List[ImageMetadata]:
    """
    Get a list of all uploaded images.
    
    Args:
        skip: Number of images to skip (for pagination)
        limit: Maximum number of images to return
    
    Returns:
        List of image metadata
    """
    try:
        stmt = select(Image).offset(skip).limit(limit).order_by(Image.upload_timestamp.desc())
        result = await session.execute(stmt)
        images = result.scalars().all()
        
        return [
            ImageMetadata(
                id=image.id,
                filename=image.filename,
                content_type=image.content_type,
                file_size=image.file_size,
                upload_timestamp=image.upload_timestamp,
                processed_timestamp=image.processed_timestamp,
                processing_status=image.processing_status,
                metadata=image.image_metadata,
            )
            for image in images
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve images: {str(e)}",
        )


@router.delete(
    "/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an image",
    description="Delete an image and its associated data",
    responses={
        204: {"description": "Image deleted successfully"},
        404: {"model": ErrorResponse, "description": "Image not found"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def delete_image(
    image_id: UUID,
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """
    Delete an image and its associated data.
    
    Args:
        image_id: ID of the image to delete
    """
    try:
        stmt = select(Image).where(Image.id == image_id)
        result = await session.execute(stmt)
        image = result.scalar_one_or_none()
        
        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found",
            )
        
        await session.delete(image)
        await session.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete image: {str(e)}",
        )