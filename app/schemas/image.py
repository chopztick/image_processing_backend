"""
Pydantic schemas for image-related operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ImageBase(BaseModel):
    """
    Base schema for image operations.
    """
    
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type of the file")
    file_size: int = Field(..., gt=0, description="File size in bytes")


class ImageCreate(ImageBase):
    """
    Schema for creating a new image record.
    """
    
    embedding_vector: List[float] = Field(..., description="Image embedding vector")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @field_validator("embedding_vector")
    @classmethod
    def validate_embedding_dimension(cls, v):
        """
        Validate that the embedding vector has the correct dimension.
        """
        from app.core.config import settings
        
        if len(v) != settings.EMBEDDING_DIMENSION:
            raise ValueError(
                f"Embedding vector must have {settings.EMBEDDING_DIMENSION} dimensions, "
                f"got {len(v)}"
            )
        return v


class ImageResponse(ImageBase):
    """
    Schema for image response data.
    """
    
    id: UUID = Field(..., description="Unique image identifier")
    upload_timestamp: datetime = Field(..., description="When the image was uploaded")
    processed_timestamp: Optional[datetime] = Field(None, description="When processing completed")
    processing_status: str = Field(..., description="Current processing status")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    model_config = {"from_attributes": True}


class ImageMetadata(BaseModel):
    """
    Schema for image metadata without embedding data.
    """
    
    id: UUID = Field(..., description="Unique image identifier")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type of the file")
    file_size: int = Field(..., description="File size in bytes")
    upload_timestamp: datetime = Field(..., description="When the image was uploaded")
    processed_timestamp: Optional[datetime] = Field(None, description="When processing completed")
    processing_status: str = Field(..., description="Current processing status")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    model_config = {"from_attributes": True}


class ImageUploadResponse(BaseModel):
    """
    Schema for image upload response.
    """
    
    id: UUID = Field(..., description="Unique image identifier")
    filename: str = Field(..., description="Original filename")
    message: str = Field(..., description="Upload status message")
    processing_status: str = Field(..., description="Current processing status")


class SimilarImage(BaseModel):
    """
    Schema for similar image results.
    """
    
    id: UUID = Field(..., description="Unique image identifier")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type of the file")
    similarity_score: float = Field(..., ge=0, le=1, description="Similarity score (0-1)")
    upload_timestamp: datetime = Field(..., description="When the image was uploaded")
    
    model_config = {"from_attributes": True}


class SimilarImagesResponse(BaseModel):
    """
    Schema for similar images search response.
    """
    
    query_image_id: UUID = Field(..., description="ID of the query image")
    similar_images: List[SimilarImage] = Field(..., description="List of similar images")
    total_results: int = Field(..., description="Total number of similar images found")
    search_timestamp: datetime = Field(..., description="When the search was performed")


class HealthResponse(BaseModel):
    """
    Schema for health check response.
    """
    
    status: str = Field(..., description="Service status")
    database_connected: bool = Field(..., description="Database connection status")
    pgvector_available: bool = Field(..., description="pgvector extension availability")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Service version")


class ErrorResponse(BaseModel):
    """
    Schema for error responses.
    """
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(..., description="Error timestamp")