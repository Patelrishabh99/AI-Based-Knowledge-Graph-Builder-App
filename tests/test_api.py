"""
API endpoint tests.
Tests the FastAPI endpoints using the test client with mocked services.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_check(self, api_client):
        """Health endpoint should return 200."""
        with patch("backend.services.neo4j_service.check_connection", return_value=False):
            with patch("backend.services.rag_service.check_pinecone_connection", return_value=False):
                response = api_client.get("/api/health")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
                assert "neo4j_connected" in data
                assert "pinecone_connected" in data


class TestModelsEndpoint:
    """Test the models listing endpoint."""

    def test_list_models(self, api_client):
        """Should return available LLM models."""
        response = api_client.get("/api/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "default" in data
        assert isinstance(data["models"], list)
        assert len(data["models"]) > 0


class TestSessionEndpoints:
    """Test session management endpoints."""

    def test_create_session(self, api_client):
        """Should create a new session."""
        response = api_client.post("/api/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data

    def test_list_sessions(self, api_client):
        """Should list sessions."""
        response = api_client.get("/api/sessions")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestQueryEndpoint:
    """Test the main query endpoint."""

    def test_query_with_mocks(self, api_client, mock_neo4j):
        """Query endpoint should process and return response."""
        with patch("backend.services.cypher_generator.generate_cypher") as mock_cypher:
            mock_cypher.return_value = {
                "cypher": "MATCH (p:Product) RETURN p LIMIT 5",
                "raw_results": [{"name": "Widget"}],
                "answer": "Found Widget",
            }
            with patch("backend.services.rag_service.hybrid_search", return_value=""):
                with patch("backend.services.llm_service.generate_response") as mock_llm:
                    mock_llm.return_value = {
                        "answer": "The top product is Widget",
                        "model": "test-model",
                        "latency_ms": 500,
                        "token_usage": {"total_tokens": 100},
                    }

                    response = api_client.post("/api/query", json={
                        "query": "top products",
                        "use_rag": False,
                    })
                    assert response.status_code == 200
                    data = response.json()
                    assert "answer" in data
                    assert "query" in data


class TestDashboardEndpoint:
    """Test the dashboard endpoint."""

    def test_dashboard(self, api_client):
        """Dashboard should return metrics."""
        with patch("backend.services.neo4j_service.get_graph_stats") as mock_stats:
            mock_stats.return_value = {
                "total_nodes": 100,
                "total_relationships": 200,
                "node_labels": ["Customer", "Product"],
                "relationship_types": ["PLACED"],
            }
            response = api_client.get("/api/dashboard")
            assert response.status_code == 200
            data = response.json()
            assert "total_queries" in data
            assert "avg_response_time_ms" in data
