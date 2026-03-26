"""
Tests for the RAG service and Query Intelligence.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestSemanticSearch:
    """Test semantic search functionality."""

    def test_semantic_search_with_results(self, mock_pinecone):
        """Should return semantic search results."""
        from backend.services.rag_service import semantic_search
        with patch("backend.services.rag_service.embed_text", return_value=[0.1] * 384):
            results = semantic_search("test query", top_k=5)
            assert len(results) > 0
            assert results[0]["id"] == "product_1"
            assert results[0]["score"] == 0.95

    def test_semantic_search_no_index(self):
        """Should return empty list if Pinecone unavailable."""
        from backend.services.rag_service import semantic_search
        with patch("backend.services.rag_service.get_pinecone_index", return_value=None):
            results = semantic_search("test query")
            assert results == []


class TestKeywordSearch:
    """Test keyword search functionality."""

    def test_keyword_search_basic(self):
        """Should perform keyword search on Neo4j."""
        from backend.services.rag_service import keyword_search
        with patch("backend.services.neo4j_service.execute_cypher") as mock_exec:
            mock_exec.return_value = [
                {"type": "Product", "props": {"product_name": "Widget", "category": "Electronics"}}
            ]
            results = keyword_search("widget electronics", limit=5)
            assert len(results) > 0

    def test_keyword_search_short_terms(self):
        """Should skip very short keywords."""
        from backend.services.rag_service import keyword_search
        with patch("backend.services.neo4j_service.execute_cypher") as mock_exec:
            mock_exec.return_value = []
            results = keyword_search("a b c", limit=5)
            assert results == []


class TestQueryIntelligence:
    """Test query intelligence service."""

    def test_detect_aggregate_intent(self):
        """Should detect aggregate intent."""
        from backend.services.query_intelligence import detect_intent
        assert detect_intent("What are the top 5 products?") == "aggregate"
        assert detect_intent("Total sales amount") == "aggregate"

    def test_detect_lookup_intent(self):
        """Should detect lookup intent."""
        from backend.services.query_intelligence import detect_intent
        assert detect_intent("Show me all customers") == "lookup"
        assert detect_intent("Who placed the most orders?") in ["aggregate", "lookup"]

    def test_detect_comparison_intent(self):
        """Should detect comparison intent."""
        from backend.services.query_intelligence import detect_intent
        assert detect_intent("Compare products vs categories") == "comparison"

    def test_extract_entities(self):
        """Should extract relevant entities."""
        from backend.services.query_intelligence import extract_entities
        entities = extract_entities("Show me customer orders")
        labels = [e["entity"] for e in entities]
        assert "Customer" in labels or "Order" in labels

    def test_extract_numeric_constraints(self):
        """Should extract numeric constraints."""
        from backend.services.query_intelligence import extract_numeric_constraints
        constraints = extract_numeric_constraints("top 10 products in 2023")
        assert constraints.get("limit") == 10
        assert constraints.get("year") == 2023

    def test_analyze_query(self):
        """Should return full analysis."""
        from backend.services.query_intelligence import analyze_query
        with patch("backend.services.query_intelligence.get_schema", return_value="mock schema"):
            analysis = analyze_query("Top 5 customers by orders")
            assert "intent" in analysis
            assert "entities" in analysis
            assert "constraints" in analysis
            assert "complexity" in analysis


class TestSessionService:
    """Test session management."""

    def test_create_session(self):
        """Should create a session."""
        from backend.services.session_service import create_session
        session_id = create_session()
        assert isinstance(session_id, str)
        assert len(session_id) > 0

    def test_add_and_retrieve(self):
        """Should store and retrieve query history."""
        from backend.services.session_service import create_session, add_query_to_session, get_session
        sid = create_session()
        add_query_to_session(sid, "test query", "test response", cypher="MATCH (n) RETURN n", model="test")
        session = get_session(sid)
        assert len(session["queries"]) == 1
        assert session["queries"][0]["query"] == "test query"

    def test_session_context(self):
        """Should build context from recent queries."""
        from backend.services.session_service import create_session, add_query_to_session, get_session_context
        sid = create_session()
        add_query_to_session(sid, "query 1", "response 1")
        add_query_to_session(sid, "query 2", "response 2")
        context = get_session_context(sid, last_n=2)
        assert "query 1" in context
        assert "query 2" in context


class TestMetricsService:
    """Test metrics tracking."""

    def test_record_and_retrieve(self):
        """Should record queries and compute metrics."""
        from backend.services.metrics_service import record_query, get_dashboard_metrics, reset_metrics
        reset_metrics()
        record_query("test query", 500.0, "test-model", success=True)
        record_query("test query 2", 300.0, "test-model", success=True)

        metrics = get_dashboard_metrics()
        assert metrics["total_queries"] == 2
        assert metrics["avg_response_time_ms"] == 400.0
        assert metrics["model_usage"]["test-model"] == 2
        assert metrics["success_rate"] == 100.0

    def test_error_tracking(self):
        """Should track errors."""
        from backend.services.metrics_service import record_query, get_dashboard_metrics, reset_metrics
        reset_metrics()
        record_query("bad query", 100.0, "model", success=False)
        metrics = get_dashboard_metrics()
        assert metrics["error_count"] == 1
        assert metrics["success_rate"] == 0.0
