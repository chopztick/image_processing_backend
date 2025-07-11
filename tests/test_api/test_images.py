"""
Tests for image API endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.image import Image
from app.services.image_processing import ImageProcessingService


class TestImageUpload:
    """
    Tests for image upload endpoint.
    """
    
    @pytest.mark.asyncio
    async def test_upload_valid_image(
        self,
        client: AsyncClient,
        sample_image_bytes: bytes,
        test_upload_helper,
    ):
        """
        Test uploading a valid image file.
        """
        files = test_upload_helper.create_upload_file(
            sample_image_bytes,
            "test_image.jpg",
            "image/jpeg"
        )
        
        response = await client.post("/api/v1/images/upload", files=files)
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["filename"] == "test_image.jpg"
        assert data["message"] == "Image uploaded and processed successfully"
        assert data["processing_status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_upload_png_image(
        self,
        client: AsyncClient,
        sample_png_bytes: bytes,
        test_upload_helper,
    ):
        """
        Test uploading a PNG image file.
        """
        files = test_upload_helper.create_upload_file(
            sample_png_bytes,
            "test_image.png",
            "image/png"
        )
        
        response = await client.post("/api/v1/images/upload", files=files)
        
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test_image.png"
    
    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(
        self,
        client: AsyncClient,
        invalid_file_bytes: bytes,
        test_upload_helper,
    ):
        """
        Test uploading an invalid file type.
        """
        files = test_upload_helper.create_upload_file(
            invalid_file_bytes,
            "test.txt",
            "text/plain"
        )
        
        response = await client.post("/api/v1/images/upload", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert "File must be an image" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_upload_invalid_image_content(
        self,
        client: AsyncClient,
        invalid_file_bytes: bytes,
        test_upload_helper,
    ):
        """
        Test uploading invalid image content with image MIME type.
        """
        files = test_upload_helper.create_upload_file(
            invalid_file_bytes,
            "fake_image.jpg",
            "image/jpeg"
        )
        
        response = await client.post("/api/v1/images/upload", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid image file" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_upload_no_file(self, client: AsyncClient):
        """
        Test uploading without providing a file.
        """
        response = await client.post("/api/v1/images/upload")
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_upload_empty_file(
        self,
        client: AsyncClient,
        test_upload_helper,
    ):
        """
        Test uploading an empty file.
        """
        files = test_upload_helper.create_upload_file(
            b"",
            "empty.jpg",
            "image/jpeg"
        )
        
        response = await client.post("/api/v1/images/upload", files=files)
        
        assert response.status_code == 400


class TestImageRetrieval:
    """
    Tests for image metadata retrieval endpoint.
    """
    
    @pytest.mark.asyncio
    async def test_get_existing_image(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
        mock_embedding: list,
    ):
        """
        Test retrieving metadata for an existing image.
        """
        # Create a test image in the database
        test_image = Image(
            filename="test_image.jpg",
            original_filename="test_image.jpg",
            content_type="image/jpeg",
            file_size=1024,
            embedding_vector=mock_embedding,
            processing_status="completed",
        )
        test_db.add(test_image)
        await test_db.commit()
        await test_db.refresh(test_image)
        
        response = await client.get(f"/api/v1/images/{test_image.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_image.id)
        assert data["filename"] == "test_image.jpg"
        assert data["content_type"] == "image/jpeg"
        assert data["file_size"] == 1024
        assert data["processing_status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_image(self, client: AsyncClient):
        """
        Test retrieving metadata for a non-existent image.
        """
        fake_id = "550e8400-e29b-41d4-a716-446655440000"
        response = await client.get(f"/api/v1/images/{fake_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_get_image_invalid_uuid(self, client: AsyncClient):
        """
        Test retrieving metadata with an invalid UUID.
        """
        response = await client.get("/api/v1/images/invalid-uuid")
        
        assert response.status_code == 422


class TestSimilaritySearch:
    """
    Tests for similarity search endpoint.
    """
    
    @pytest.mark.asyncio
    async def test_find_similar_images(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
        mock_embedding: list,
    ):
        """
        Test finding similar images for an existing image.
        """
        # Create test images with similar embeddings
        query_image = Image(
            filename="query_image.jpg",
            original_filename="query_image.jpg",
            content_type="image/jpeg",
            file_size=1024,
            embedding_vector=mock_embedding,
            processing_status="completed",
        )
        
        # Create a similar image (slightly different embedding)
        similar_embedding = mock_embedding.copy()
        similar_embedding[0] += 0.01  # Small change
        similar_image = Image(
            filename="similar_image.jpg",
            original_filename="similar_image.jpg",
            content_type="image/jpeg",
            file_size=1024,
            embedding_vector=similar_embedding,
            processing_status="completed",
        )
        
        test_db.add_all([query_image, similar_image])
        await test_db.commit()
        await test_db.refresh(query_image)
        await test_db.refresh(similar_image)
        
        response = await client.get(f"/api/v1/images/{query_image.id}/similar")
        
        assert response.status_code == 200
        data = response.json()
        assert data["query_image_id"] == str(query_image.id)
        assert isinstance(data["similar_images"], list)
        assert data["total_results"] >= 0
        assert "search_timestamp" in data
    
    @pytest.mark.asyncio
    async def test_find_similar_with_parameters(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
        mock_embedding: list,
    ):
        """
        Test finding similar images with custom parameters.
        """
        query_image = Image(
            filename="query_image.jpg",
            original_filename="query_image.jpg",
            content_type="image/jpeg",
            file_size=1024,
            embedding_vector=mock_embedding,
            processing_status="completed",
        )
        test_db.add(query_image)
        await test_db.commit()
        await test_db.refresh(query_image)
        
        response = await client.get(
            f"/api/v1/images/{query_image.id}/similar",
            params={"limit": 5, "threshold": 0.8}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["similar_images"]) <= 5
    
    @pytest.mark.asyncio
    async def test_find_similar_nonexistent_image(self, client: AsyncClient):
        """
        Test finding similar images for a non-existent image.
        """
        fake_id = "550e8400-e29b-41d4-a716-446655440000"
        response = await client.get(f"/api/v1/images/{fake_id}/similar")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]


class TestImageListing:
    """
    Tests for image listing endpoint.
    """
    
    @pytest.mark.asyncio
    async def test_list_empty_images(self, client: AsyncClient):
        """
        Test listing images when there are none.
        """
        response = await client.get("/api/v1/images/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    @pytest.mark.asyncio
    async def test_list_images_with_data(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
        mock_embedding: list,
    ):
        """
        Test listing images when there are some in the database.
        """
        # Create test images
        for i in range(3):
            image = Image(
                filename=f"test_image_{i}.jpg",
                original_filename=f"test_image_{i}.jpg",
                content_type="image/jpeg",
                file_size=1024,
                embedding_vector=mock_embedding,
                processing_status="completed",
            )
            test_db.add(image)
        
        await test_db.commit()
        
        response = await client.get("/api/v1/images/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        
        # Check structure of first item
        first_image = data[0]
        assert "id" in first_image
        assert "filename" in first_image
        assert "content_type" in first_image
        assert "file_size" in first_image
        assert "upload_timestamp" in first_image
    
    @pytest.mark.asyncio
    async def test_list_images_with_pagination(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
        mock_embedding: list,
    ):
        """
        Test listing images with pagination parameters.
        """
        # Create test images
        for i in range(5):
            image = Image(
                filename=f"test_image_{i}.jpg",
                original_filename=f"test_image_{i}.jpg",
                content_type="image/jpeg",
                file_size=1024,
                embedding_vector=mock_embedding,
                processing_status="completed",
            )
            test_db.add(image)
        
        await test_db.commit()
        
        # Test with limit
        response = await client.get("/api/v1/images/", params={"limit": 3})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        # Test with skip and limit
        response = await client.get("/api/v1/images/", params={"skip": 2, "limit": 2})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestImageDeletion:
    """
    Tests for image deletion endpoint.
    """
    
    @pytest.mark.asyncio
    async def test_delete_existing_image(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
        mock_embedding: list,
    ):
        """
        Test deleting an existing image.
        """
        # Create a test image
        test_image = Image(
            filename="test_image.jpg",
            original_filename="test_image.jpg",
            content_type="image/jpeg",
            file_size=1024,
            embedding_vector=mock_embedding,
            processing_status="completed",
        )
        test_db.add(test_image)
        await test_db.commit()
        await test_db.refresh(test_image)
        
        response = await client.delete(f"/api/v1/images/{test_image.id}")
        
        assert response.status_code == 204
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_image(self, client: AsyncClient):
        """
        Test deleting a non-existent image.
        """
        fake_id = "550e8400-e29b-41d4-a716-446655440000"
        response = await client.delete(f"/api/v1/images/{fake_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]