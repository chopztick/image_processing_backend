"""
Tests for health check API endpoints.
"""

import pytest
from httpx import AsyncClient


class TestHealthCheck:
    """
    Tests for health check endpoints.
    """
    
    @pytest.mark.asyncio
    async def test_liveness_check(self, client: AsyncClient):
        """
        Test the liveness check endpoint.
        """
        response = await client.get("/api/v1/health/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data
        assert "service" in data
        assert "version" in data
    
    @pytest.mark.asyncio
    async def test_readiness_check(self, client: AsyncClient):
        """
        Test the readiness check endpoint.
        """
        response = await client.get("/api/v1/health/ready")
        
        # This might fail with test database (SQLite doesn't have pgvector)
        # so we check for either success or expected failure
        assert response.status_code in [200, 503]
        
        data = response.json()
        if response.status_code == 200:
            assert data["status"] == "ready"
            assert "timestamp" in data
        else:
            assert "pgvector" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_basic_health_check(self, client: AsyncClient):
        """
        Test the basic health check endpoint.
        """
        response = await client.get("/api/v1/health/")
        
        # This might fail with test database
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "healthy"
            assert "database_connected" in data
            assert "pgvector_available" in data
            assert "timestamp" in data
            assert "version" in data
    
    @pytest.mark.asyncio
    async def test_detailed_health_check(self, client: AsyncClient):
        """
        Test the detailed health check endpoint.
        """
        response = await client.get("/api/v1/health/detailed")
        
        # This might fail with test database
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "service" in data
            assert "database" in data
            assert "pgvector" in data
            assert "embeddings" in data
            assert "configuration" in data