"""
Test configuration and fixtures for the Image Processing Service.
"""

import asyncio
import io
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from PIL import Image as PILImage
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.database import Base, get_async_session
from app.core.config import settings
from app.main import app


# Test database URL (using PostgreSQL for testing to support pgvector)
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:password@postgres:5432/test_image_processing"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
)

# Test session factory
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create an instance of the default event loop for the test session.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.
    """
    from sqlalchemy import text
    
    # Create tables and enable pgvector extension
    async with test_engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
    
    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client with test database.
    """
    def get_test_db():
        return test_db
    
    app.dependency_overrides[get_async_session] = get_test_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sync_client() -> TestClient:
    """
    Create a synchronous test client for simple tests.
    """
    return TestClient(app)


@pytest.fixture
def sample_image_bytes() -> bytes:
    """
    Create a sample image as bytes for testing.
    """
    # Create a simple test image
    img = PILImage.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    return img_bytes.getvalue()


@pytest.fixture
def sample_image_file(sample_image_bytes: bytes):
    """
    Create a sample image file-like object for testing.
    """
    return io.BytesIO(sample_image_bytes)


@pytest.fixture
def sample_png_bytes() -> bytes:
    """
    Create a sample PNG image as bytes for testing.
    """
    img = PILImage.new("RGBA", (50, 50), color=(0, 255, 0, 128))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    return img_bytes.getvalue()


@pytest.fixture
def invalid_file_bytes() -> bytes:
    """
    Create invalid file content for testing error cases.
    """
    return b"This is not an image file"


@pytest.fixture
def large_image_bytes() -> bytes:
    """
    Create a large image for testing file size limits.
    """
    # Create a large image (should exceed MAX_FILE_SIZE for testing)
    img = PILImage.new("RGB", (2000, 2000), color="blue")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG", quality=100)
    return img_bytes.getvalue()


@pytest.fixture
def mock_embedding() -> list:
    """
    Create a mock embedding vector for testing.
    """
    import math
    import random
    
    # Generate a normalized vector
    vector = [random.uniform(-1, 1) for _ in range(settings.EMBEDDING_DIMENSION)]
    norm = math.sqrt(sum(x**2 for x in vector))
    if norm > 0:
        vector = [x / norm for x in vector]
    return vector


@pytest.fixture
def test_image_metadata() -> dict:
    """
    Create test image metadata.
    """
    return {
        "filename": "test_image.jpg",
        "content_type": "image/jpeg",
        "file_size": 1024,
        "metadata": {
            "format": "JPEG",
            "mode": "RGB",
            "size": [100, 100],
            "width": 100,
            "height": 100,
        }
    }


class TestImageUpload:
    """
    Helper class for creating test image uploads.
    """
    
    @staticmethod
    def create_upload_file(content: bytes, filename: str = "test.jpg", content_type: str = "image/jpeg"):
        """
        Create a file upload object for testing.
        """
        return {
            "file": (filename, io.BytesIO(content), content_type)
        }


@pytest.fixture
def test_upload_helper():
    """
    Provide the TestImageUpload helper class.
    """
    return TestImageUpload