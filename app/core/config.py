"""
Configuration settings for the Image Processing Service.
"""

from functools import lru_cache
from typing import Any, Optional, List
import os
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    """
    
    PROJECT_NAME: str = "Image Processing Service"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "1.0.0"
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8000",
    ]
    
    # Database settings
    POSTGRES_DB: str = "image_processing"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> str:
        """
        Assemble database URL from individual components.
        """
        if isinstance(v, str):
            return v
        # Access field values through info.data
        values = info.data if hasattr(info, 'data') else {}
        return str(PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("POSTGRES_USER", "postgres"),
            password=values.get("POSTGRES_PASSWORD", "password"),
            host=values.get("POSTGRES_HOST", "localhost"),
            port=values.get("POSTGRES_PORT", 5432),
            path=values.get("POSTGRES_DB", "image_processing"),
        ))
    
    # File upload settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
    UPLOAD_DIR: str = "uploads"
    
    # Vector embedding settings
    EMBEDDING_DIMENSION: int = 512
    SIMILARITY_THRESHOLD: float = 0.7
    MAX_SIMILAR_RESULTS: int = 10
    
    # Application settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    """
    return Settings()


# Global settings instance
settings = get_settings()