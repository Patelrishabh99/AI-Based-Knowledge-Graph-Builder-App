"""
Tests for the FAISS vector store service.
"""

import pytest
from unittest.mock import patch, MagicMock
import numpy as np


class TestFAISSService:
    """Test FAISS service functionality."""

    def test_embed_text(self):
        """Should generate embedding vector."""
        with patch("backend.services.faiss_service._get_embedding_model") as mock_model:
            mock_encoder = MagicMock()
            mock_encoder.encode.return_value = np.random.rand(384).astype(np.float32)
            mock_model.return_value = mock_encoder

            from backend.services.faiss_service import _embed_text
            result = _embed_text("test query")
            assert isinstance(result, list)
            assert len(result) == 384

    def test_index_graph_data_no_data(self):
        """Should handle empty graph gracefully."""
        with patch("backend.services.neo4j_service.execute_cypher", return_value=[]):
            from backend.services.faiss_service import index_graph_data
            result = index_graph_data()
            assert result["status"] == "warning"
            assert result["count"] == 0

    def test_semantic_search_no_index(self):
        """Should return empty results when no index exists."""
        from backend.services import faiss_service
        faiss_service._faiss_index = None
        faiss_service._faiss_metadata = []

        with patch("backend.services.faiss_service.load_index", return_value=False):
            results, latency = faiss_service.semantic_search("test query")
            assert results == []
            assert latency == 0.0

    def test_check_faiss_connection_no_index(self):
        """Should return False when no index is loaded."""
        from backend.services import faiss_service
        faiss_service._faiss_index = None

        with patch("backend.services.faiss_service.load_index", return_value=False):
            assert faiss_service.check_faiss_connection() is False

    def test_get_index_stats_no_index(self):
        """Should return empty stats when no index."""
        from backend.services import faiss_service
        faiss_service._faiss_index = None

        with patch("backend.services.faiss_service.load_index", return_value=False):
            stats = faiss_service.get_index_stats()
            assert stats["loaded"] is False
            assert stats["total_vectors"] == 0


class TestVectorDBBenchmark:
    """Test vector DB benchmark service."""

    def test_comparison_properties(self):
        """Should return static comparison properties."""
        from backend.services.vectordb_benchmark import get_comparison_properties
        props = get_comparison_properties()
        assert "faiss" in props
        assert "pinecone" in props
        assert props["faiss"]["name"] == "FAISS"
        assert props["pinecone"]["name"] == "Pinecone"
        assert "hosting" in props["faiss"]
        assert "cost" in props["faiss"]

    def test_run_benchmark_empty(self):
        """Should handle benchmark with no data gracefully."""
        with patch("backend.services.faiss_service.semantic_search", return_value=([], 0.0)):
            with patch("backend.services.rag_service.semantic_search", return_value=[]):
                from backend.services.vectordb_benchmark import run_benchmark
                result = run_benchmark("test query", top_k=5)
                assert "faiss" in result
                assert "pinecone" in result
                assert "recommendation" in result
                assert result["recommendation"]["production_choice"] == "Pinecone"

    def test_recommendation_always_pinecone(self):
        """Recommendation should always favor Pinecone for production."""
        from backend.services.vectordb_benchmark import _generate_recommendation
        result = _generate_recommendation({
            "faiss": {"latency_ms": 0.5},
            "pinecone": {"latency_ms": 45.0},
        })
        assert result["production_choice"] == "Pinecone"
        assert result["speed_winner"] == "FAISS"
