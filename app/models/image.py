"""
Image model with pgvector support for the Image Processing Service.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Integer, String, JSON, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from pgvector.sqlalchemy import Vector

from app.core.database import Base
from app.core.config import settings


class Image(Base):
    """
    Image model for storing image metadata and embeddings.
    
    This model stores image metadata along with vector embeddings
    for similarity search using pgvector.
    """
    
    __tablename__ = "images"
    
    # Primary key
    id: UUID = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    
    # File metadata
    filename: str = Column(String(255), nullable=False)
    original_filename: str = Column(String(255), nullable=False)
    content_type: str = Column(String(100), nullable=False)
    file_size: int = Column(Integer, nullable=False)
    file_path: str = Column(String(512), nullable=True)
    
    # Timestamps
    upload_timestamp: datetime = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    processed_timestamp: Optional[datetime] = Column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Vector embedding for similarity search
    embedding_vector: List[float] = Column(
        Vector(settings.EMBEDDING_DIMENSION),
        nullable=False,
    )
    
    # Additional metadata  
    image_metadata: Optional[Dict[str, Any]] = Column(JSON, nullable=True)
    
    # Processing status
    processing_status: str = Column(
        String(50),
        default="pending",
        nullable=False,
    )
    
    def __repr__(self) -> str:
        """
        String representation of the Image model.
        """
        return (
            f"Image(id={self.id}, filename='{self.filename}', "
            f"content_type='{self.content_type}', "
            f"file_size={self.file_size}, "
            f"status='{self.processing_status}')"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Image model to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the image
        """
        return {
            "id": str(self.id),
            "filename": self.filename,
            "original_filename": self.original_filename,
            "content_type": self.content_type,
            "file_size": self.file_size,
            "file_path": self.file_path,
            "upload_timestamp": self.upload_timestamp.isoformat() if self.upload_timestamp else None,
            "processed_timestamp": self.processed_timestamp.isoformat() if self.processed_timestamp else None,
            "processing_status": self.processing_status,
            "metadata": self.image_metadata,
            "embedding_dimension": len(self.embedding_vector) if self.embedding_vector else 0,
        }