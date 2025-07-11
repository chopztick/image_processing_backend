"""
Tests for image processing service.
"""

import pytest
from fastapi import HTTPException

from app.services.image_processing import ImageProcessingService


class TestImageProcessingService:
    """
    Tests for the ImageProcessingService.
    """
    
    def test_validate_valid_image(self, sample_image_bytes: bytes):
        """
        Test validating a valid image.
        """
        # Should not raise an exception
        ImageProcessingService.validate_image(
            content=sample_image_bytes,
            content_type="image/jpeg",
            filename="test.jpg"
        )
    
    def test_validate_invalid_content_type(self, sample_image_bytes: bytes):
        """
        Test validating an image with invalid content type.
        """
        with pytest.raises(HTTPException) as exc_info:
            ImageProcessingService.validate_image(
                content=sample_image_bytes,
                content_type="text/plain",
                filename="test.txt"
            )
        assert exc_info.value.status_code == 400
        assert "File must be an image" in str(exc_info.value.detail)
    
    def test_validate_invalid_extension(self, sample_image_bytes: bytes):
        """
        Test validating an image with invalid file extension.
        """
        with pytest.raises(HTTPException) as exc_info:
            ImageProcessingService.validate_image(
                content=sample_image_bytes,
                content_type="image/jpeg",
                filename="test.txt"
            )
        assert exc_info.value.status_code == 400
        assert "File extension not allowed" in str(exc_info.value.detail)
    
    def test_validate_invalid_image_content(self, invalid_file_bytes: bytes):
        """
        Test validating invalid image content.
        """
        with pytest.raises(HTTPException) as exc_info:
            ImageProcessingService.validate_image(
                content=invalid_file_bytes,
                content_type="image/jpeg",
                filename="test.jpg"
            )
        assert exc_info.value.status_code == 400
        assert "Invalid image file" in str(exc_info.value.detail)
    
    def test_extract_image_metadata(self, sample_image_bytes: bytes):
        """
        Test extracting metadata from a valid image.
        """
        metadata = ImageProcessingService.extract_image_metadata(sample_image_bytes)
        
        assert isinstance(metadata, dict)
        assert "format" in metadata
        assert "mode" in metadata
        assert "size" in metadata
        assert "width" in metadata
        assert "height" in metadata
        assert metadata["width"] == 100
        assert metadata["height"] == 100
    
    def test_extract_metadata_invalid_image(self, invalid_file_bytes: bytes):
        """
        Test extracting metadata from invalid image content.
        """
        metadata = ImageProcessingService.extract_image_metadata(invalid_file_bytes)
        
        assert isinstance(metadata, dict)
        assert metadata["format"] == "unknown"
        assert "extraction_error" in metadata
    
    def test_generate_mock_embedding_consistency(self, sample_image_bytes: bytes):
        """
        Test that mock embedding generation is consistent.
        """
        embedding1 = ImageProcessingService.generate_mock_embedding(
            sample_image_bytes, "test.jpg"
        )
        embedding2 = ImageProcessingService.generate_mock_embedding(
            sample_image_bytes, "test.jpg"
        )
        
        assert embedding1 == embedding2
        assert len(embedding1) == 512  # Default embedding dimension
    
    def test_generate_mock_embedding_different_inputs(self, sample_image_bytes: bytes):
        """
        Test that different inputs produce different embeddings.
        """
        embedding1 = ImageProcessingService.generate_mock_embedding(
            sample_image_bytes, "test1.jpg"
        )
        embedding2 = ImageProcessingService.generate_mock_embedding(
            sample_image_bytes, "test2.jpg"
        )
        
        assert embedding1 != embedding2
        assert len(embedding1) == len(embedding2)
    
    def test_mock_embedding_normalization(self, sample_image_bytes: bytes):
        """
        Test that mock embeddings are properly normalized.
        """
        import math
        
        embedding = ImageProcessingService.generate_mock_embedding(
            sample_image_bytes, "test.jpg"
        )
        
        # Calculate L2 norm
        norm = math.sqrt(sum(x**2 for x in embedding))
        
        # Should be normalized (close to 1.0)
        assert abs(norm - 1.0) < 0.001
    
    @pytest.mark.asyncio
    async def test_process_image_success(self, sample_image_bytes: bytes):
        """
        Test successful image processing.
        """
        embedding, metadata = await ImageProcessingService.process_image(
            content=sample_image_bytes,
            filename="test.jpg",
            content_type="image/jpeg"
        )
        
        assert isinstance(embedding, list)
        assert len(embedding) == 512
        assert isinstance(metadata, dict)
        assert "processing_timestamp" in metadata
        assert "embedding_method" in metadata
        assert metadata["embedding_method"] == "mock_hash_based"
    
    @pytest.mark.asyncio
    async def test_process_image_validation_error(self, invalid_file_bytes: bytes):
        """
        Test image processing with validation error.
        """
        with pytest.raises(HTTPException):
            await ImageProcessingService.process_image(
                content=invalid_file_bytes,
                filename="test.txt",
                content_type="text/plain"
            )
    
    def test_preprocess_image(self, sample_image_bytes: bytes):
        """
        Test image preprocessing.
        """
        preprocessed = ImageProcessingService.preprocess_image(
            sample_image_bytes,
            target_size=(128, 128)
        )
        
        assert isinstance(preprocessed, bytes)
        assert len(preprocessed) > 0
        
        # Verify the processed image is valid
        from PIL import Image
        import io
        
        with Image.open(io.BytesIO(preprocessed)) as img:
            assert img.size == (128, 128)
            assert img.mode == "RGB"