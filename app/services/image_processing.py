"""
Image processing service with mock embedding generation.
"""

import hashlib
import io
import math
import random
from typing import List, Tuple, Dict, Any
from datetime import datetime

from PIL import Image
from fastapi import HTTPException

from app.core.config import settings


class ImageProcessingService:
    """
    Service for processing images and generating mock embeddings.
    """
    
    @staticmethod
    def validate_image(content: bytes, content_type: str, filename: str) -> None:
        """
        Validate image content and metadata.
        
        Args:
            content: Image file content
            content_type: MIME type of the file
            filename: Original filename
            
        Raises:
            HTTPException: If validation fails
        """
        # Check file size
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"
            )
        
        # Check content type
        if not content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )
        
        # Check file extension
        file_extension = filename.lower().split(".")[-1] if "." in filename else ""
        if f".{file_extension}" not in [ext.lower() for ext in settings.ALLOWED_EXTENSIONS]:
            raise HTTPException(
                status_code=400,
                detail=f"File extension not allowed. Allowed extensions: {settings.ALLOWED_EXTENSIONS}"
            )
        
        # Try to open the image to verify it's valid
        try:
            with Image.open(io.BytesIO(content)) as img:
                # Basic image validation
                img.verify()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image file: {str(e)}"
            )
    
    @staticmethod
    def extract_image_metadata(content: bytes) -> Dict[str, Any]:
        """
        Extract metadata from image content.
        
        Args:
            content: Image file content
            
        Returns:
            Dict containing image metadata
        """
        try:
            with Image.open(io.BytesIO(content)) as img:
                metadata = {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "width": img.size[0],
                    "height": img.size[1],
                    "has_transparency": img.mode in ("RGBA", "LA") or "transparency" in img.info,
                }
                
                # Add EXIF data if available
                if hasattr(img, "_getexif") and img._getexif():
                    exif = img._getexif()
                    if exif:
                        metadata["exif"] = {
                            str(k): str(v) for k, v in exif.items() 
                            if isinstance(v, (str, int, float))
                        }
                
                return metadata
        except Exception as e:
            # Return basic metadata if extraction fails
            return {
                "format": "unknown",
                "mode": "unknown",
                "size": [0, 0],
                "width": 0,
                "height": 0,
                "has_transparency": False,
                "extraction_error": str(e),
            }
    
    @staticmethod
    def generate_mock_embedding(content: bytes, filename: str) -> List[float]:
        """
        Generate a consistent mock embedding for the image.
        
        This uses a hash-based approach to ensure the same image
        always produces the same embedding vector.
        
        Args:
            content: Image file content
            filename: Original filename
            
        Returns:
            List of floats representing the embedding vector
        """
        # Create a consistent hash from content and filename
        content_hash = hashlib.sha256(content).hexdigest()
        filename_hash = hashlib.md5(filename.encode()).hexdigest()
        combined_hash = hashlib.sha256(f"{content_hash}_{filename_hash}".encode()).hexdigest()
        
        # Use hash as seed for reproducible random generation
        random.seed(combined_hash)
        
        # Generate embedding vector
        embedding = []
        for i in range(settings.EMBEDDING_DIMENSION):
            # Use different parts of the hash to add more variation
            seed_offset = int(combined_hash[i % len(combined_hash)], 16)
            random.seed(int(combined_hash[:8], 16) + i + seed_offset)
            
            # Generate value between -1 and 1
            value = random.uniform(-1, 1)
            embedding.append(value)
        
        # Normalize the vector for cosine similarity
        norm = math.sqrt(sum(x**2 for x in embedding))
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    @staticmethod
    async def process_image(
        content: bytes,
        filename: str,
        content_type: str,
    ) -> Tuple[List[float], Dict[str, Any]]:
        """
        Process an image and generate embedding and metadata.
        
        Args:
            content: Image file content
            filename: Original filename
            content_type: MIME type of the file
            
        Returns:
            Tuple of (embedding_vector, metadata)
            
        Raises:
            HTTPException: If processing fails
        """
        # Validate the image
        ImageProcessingService.validate_image(content, content_type, filename)
        
        # Extract metadata
        metadata = ImageProcessingService.extract_image_metadata(content)
        
        # Add processing metadata
        metadata.update({
            "processing_timestamp": datetime.utcnow().isoformat(),
            "embedding_method": "mock_hash_based",
            "embedding_dimension": settings.EMBEDDING_DIMENSION,
            "processed_by": "ImageProcessingService",
        })
        
        # Generate embedding
        embedding = ImageProcessingService.generate_mock_embedding(content, filename)
        
        return embedding, metadata
    
    @staticmethod
    def preprocess_image(content: bytes, target_size: Tuple[int, int] = (224, 224)) -> bytes:
        """
        Preprocess image for consistent processing.
        
        Args:
            content: Original image content
            target_size: Target size for resizing
            
        Returns:
            Preprocessed image content
        """
        try:
            with Image.open(io.BytesIO(content)) as img:
                # Convert to RGB if necessary
                if img.mode != "RGB":
                    img = img.convert("RGB")
                
                # Resize image
                img = img.resize(target_size, Image.Resampling.LANCZOS)
                
                # Save to bytes
                output = io.BytesIO()
                img.save(output, format="JPEG", quality=85)
                return output.getvalue()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Image preprocessing failed: {str(e)}"
            )