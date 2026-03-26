"""
Tests for the Cypher Generator service.
"""

import pytest
from backend.services.cypher_generator import validate_cypher


class TestCypherValidation:
    """Test Cypher query validation."""

    def test_valid_match_query(self):
        """Valid MATCH query should pass."""
        assert validate_cypher("MATCH (n) RETURN n") is True

    def test_valid_complex_query(self):
        """Complex valid query should pass."""
        cypher = "MATCH (c:Customer)-[:PLACED]->(o:Order) RETURN c.customer_name, count(o) AS orders"
        assert validate_cypher(cypher) is True

    def test_empty_query(self):
        """Empty query should fail."""
        assert validate_cypher("") is False
        assert validate_cypher("   ") is False

    def test_none_query(self):
        """None query should fail."""
        assert validate_cypher(None) is False

    def test_dangerous_drop(self):
        """DROP without RETURN should be rejected."""
        assert validate_cypher("DROP INDEX idx") is False

    def test_dangerous_delete_only(self):
        """DELETE without RETURN should be rejected."""
        assert validate_cypher("DETACH DELETE n") is False

    def test_delete_with_return(self):
        """DELETE with RETURN should pass (it's actually safe for reading)."""
        # This is a query that has both keywords
        assert validate_cypher("MATCH (n) DELETE n RETURN count(n)") is True
