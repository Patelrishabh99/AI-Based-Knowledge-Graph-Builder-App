"""
Pytest fixtures and configuration.
Provides mock services for testing without external dependencies.
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment variables before importing any modules
os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "test"
os.environ["NEO4J_DATABASE"] = "neo4j"
os.environ["GROQ_API_KEY"] = "test-key"
os.environ["PINECONE_API_KEY"] = "test-key"
os.environ["HF_TOKEN"] = "test-token"
os.environ["API_SECRET_KEY"] = "default-secret-key"


@pytest.fixture
def mock_neo4j():
    """Mock Neo4j graph connection."""
    with patch("backend.services.neo4j_service.get_graph") as mock:
        graph = MagicMock()
        graph.schema = "Node labels: Customer, Product, Order"
        graph.query.return_value = []
        mock.return_value = graph
        yield graph


@pytest.fixture
def mock_llm():
    """Mock LLM service."""
    with patch("backend.services.llm_service.get_llm") as mock:
        llm = MagicMock()
        response = MagicMock()
        response.content = "Test AI response"
        response.response_metadata = {"token_usage": {"total_tokens": 100}}
        llm.invoke.return_value = response
        mock.return_value = llm
        yield llm


@pytest.fixture
def mock_pinecone():
    """Mock Pinecone index."""
    with patch("backend.services.rag_service.get_pinecone_index") as mock:
        index = MagicMock()
        index.query.return_value = {
            "matches": [
                {
                    "id": "product_1",
                    "score": 0.95,
                    "metadata": {"type": "Product", "text": "Product: Widget"},
                }
            ]
        }
        mock.return_value = index
        yield index


@pytest.fixture
def api_client():
    """Create a test client for the FastAPI app."""
    from fastapi.testclient import TestClient
    from backend.main import app
    return TestClient(app)
