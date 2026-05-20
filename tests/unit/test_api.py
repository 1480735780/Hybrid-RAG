"""
Unit tests for API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Tests for health endpoints."""

    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/api/v1/health/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "service" in data


class TestChatEndpoints:
    """Tests for chat endpoints."""

    def test_chat_endpoint(self, client: TestClient):
        """Test chat endpoint."""
        response = client.post(
            "/api/v1/chat/",
            json={
                "query": "MySQL connection error",
                "use_hybrid": True,
                "top_k": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "session_id" in data
        assert "sources" in data
        assert "query" in data

    def test_chat_endpoint_with_history(self, client: TestClient):
        """Test chat endpoint with history."""
        response = client.post(
            "/api/v1/chat/",
            json={
                "query": "How to fix it?",
                "history": [
                    {"role": "user", "content": "MySQL connection error"},
                    {"role": "assistant", "content": "Check MySQL service status."},
                ],
                "use_hybrid": True,
                "top_k": 5,
            },
        )

        assert response.status_code == 200

    def test_chat_endpoint_with_metadata_filter(self, client: TestClient):
        """Test chat endpoint with metadata filter."""
        response = client.post(
            "/api/v1/chat/",
            json={
                "query": "Docker container failed",
                "metadata_filter": {
                    "department": "ops",
                    "service": "docker",
                },
                "use_hybrid": True,
                "top_k": 5,
            },
        )

        assert response.status_code == 200


class TestDocumentEndpoints:
    """Tests for document endpoints."""

    def test_list_documents(self, client: TestClient):
        """Test list documents endpoint."""
        response = client.get("/api/v1/documents/")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "documents" in data


class TestKnowledgeBaseEndpoints:
    """Tests for knowledge base endpoints."""

    def test_get_stats(self, client: TestClient):
        """Test get stats endpoint."""
        response = client.get("/api/v1/knowledge-base/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_documents" in data
        assert "total_chunks" in data

    def test_search_endpoint(self, client: TestClient):
        """Test search endpoint."""
        response = client.post(
            "/api/v1/knowledge-base/search",
            json={
                "query": "MySQL troubleshooting",
                "top_k": 10,
                "use_hybrid": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert "total" in data


if __name__ == "__main__":
    pytest.main([__file__])
