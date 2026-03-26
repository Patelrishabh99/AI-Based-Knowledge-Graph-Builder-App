"""
Tests for the Neo4j service.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestNeo4jService:
    """Test Neo4j service operations."""

    def test_execute_cypher_success(self, mock_neo4j):
        """Should execute Cypher and return results."""
        mock_neo4j.query.return_value = [{"count": 42}]

        from backend.services.neo4j_service import execute_cypher
        with patch("backend.services.neo4j_service.get_graph", return_value=mock_neo4j):
            result = execute_cypher("MATCH (n) RETURN count(n) AS count")
            assert result == [{"count": 42}]

    def test_execute_cypher_empty(self, mock_neo4j):
        """Should handle empty results."""
        mock_neo4j.query.return_value = None

        from backend.services.neo4j_service import execute_cypher
        with patch("backend.services.neo4j_service.get_graph", return_value=mock_neo4j):
            result = execute_cypher("MATCH (n) RETURN n LIMIT 0")
            assert result == []

    def test_get_schema(self, mock_neo4j):
        """Should return graph schema."""
        from backend.services.neo4j_service import get_schema
        with patch("backend.services.neo4j_service.get_graph", return_value=mock_neo4j):
            schema = get_schema()
            assert isinstance(schema, str)

    def test_get_graph_stats(self, mock_neo4j):
        """Should return graph statistics."""
        from backend.services.neo4j_service import get_graph_stats
        with patch("backend.services.neo4j_service.execute_cypher") as mock_exec:
            mock_exec.side_effect = [
                [{"count": 100}],  # nodes
                [{"count": 200}],  # relationships
                [{"labels": ["Customer", "Product"]}],  # labels
                [{"types": ["PLACED", "CONTAINS"]}],  # types
            ]
            stats = get_graph_stats()
            assert stats["total_nodes"] == 100
            assert stats["total_relationships"] == 200
            assert "Customer" in stats["node_labels"]


class TestGraphVisualization:
    """Test graph visualization data extraction."""

    def test_visualization_data_structure(self, mock_neo4j):
        """Should return properly structured graph data."""
        from backend.services.neo4j_service import get_graph_visualization_data
        with patch("backend.services.neo4j_service.execute_cypher") as mock_exec:
            mock_exec.return_value = []
            data = get_graph_visualization_data(limit=10)
            assert "nodes" in data
            assert "edges" in data
            assert isinstance(data["nodes"], list)
            assert isinstance(data["edges"], list)
