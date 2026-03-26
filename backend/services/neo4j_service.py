"""
Neo4j Knowledge Graph service.
Manages connection, schema retrieval, Cypher execution, and graph data extraction.
"""

import logging
from typing import Optional
from langchain_community.graphs import Neo4jGraph
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Singleton graph connection ─────────────────────────────────
_graph: Optional[Neo4jGraph] = None


def get_graph() -> Neo4jGraph:
    """Get or create the Neo4j graph connection."""
    global _graph
    if _graph is None:
        try:
            _graph = Neo4jGraph(
                url=settings.neo4j_uri,
                username=settings.neo4j_username,
                password=settings.neo4j_password,
                database=settings.neo4j_database,
            )
            logger.info("✅ Connected to Neo4j at %s", settings.neo4j_uri)
        except Exception as e:
            logger.error("❌ Neo4j connection failed: %s", e)
            raise
    return _graph


def execute_cypher(cypher: str, params: Optional[dict] = None) -> list[dict]:
    """Execute a Cypher query and return results."""
    graph = get_graph()
    try:
        results = graph.query(cypher, params=params or {})
        return results if results else []
    except Exception as e:
        logger.error("Cypher execution error: %s | Query: %s", e, cypher)
        raise


def get_schema() -> str:
    """Get the graph schema as a string."""
    graph = get_graph()
    try:
        return graph.schema
    except Exception:
        return "Schema unavailable"


def get_graph_stats() -> dict:
    """Get graph statistics: node counts, relationship counts, labels, types."""
    try:
        node_count = execute_cypher("MATCH (n) RETURN count(n) AS count")
        rel_count = execute_cypher("MATCH ()-[r]->() RETURN count(r) AS count")
        labels = execute_cypher("CALL db.labels() YIELD label RETURN collect(label) AS labels")
        rel_types = execute_cypher(
            "CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) AS types"
        )
        return {
            "total_nodes": node_count[0]["count"] if node_count else 0,
            "total_relationships": rel_count[0]["count"] if rel_count else 0,
            "node_labels": labels[0]["labels"] if labels else [],
            "relationship_types": rel_types[0]["types"] if rel_types else [],
        }
    except Exception as e:
        logger.error("Failed to get graph stats: %s", e)
        return {"total_nodes": 0, "total_relationships": 0, "node_labels": [], "relationship_types": []}


def get_graph_visualization_data(
    node_type: Optional[str] = None,
    relationship_type: Optional[str] = None,
    limit: int = 100,
) -> dict:
    """
    Fetch nodes and relationships for 3D graph visualization.
    Returns nodes and edges with properties.
    """
    # Build dynamic Cypher based on filters
    if node_type and relationship_type:
        cypher = f"""
        MATCH (a:{node_type})-[r:{relationship_type}]->(b)
        RETURN a, r, b LIMIT {limit}
        """
    elif node_type:
        cypher = f"""
        MATCH (a:{node_type})-[r]->(b)
        RETURN a, r, b LIMIT {limit}
        """
    elif relationship_type:
        cypher = f"""
        MATCH (a)-[r:{relationship_type}]->(b)
        RETURN a, r, b LIMIT {limit}
        """
    else:
        cypher = f"""
        MATCH (a)-[r]->(b)
        RETURN a, r, b LIMIT {limit}
        """

    results = execute_cypher(cypher)
    nodes = {}
    edges = []

    for record in results:
        # Process source node
        a = record.get("a", {})
        b = record.get("b", {})
        r = record.get("r", {})

        if isinstance(a, dict):
            a_id = str(a.get("customer_id", a.get("product_id", a.get("order_id", id(a)))))
            a_labels = "Node"
            a_props = a
        else:
            a_id = str(getattr(a, "element_id", id(a)))
            a_labels = list(a.labels)[0] if hasattr(a, "labels") and a.labels else "Node"
            a_props = dict(a) if hasattr(a, "__iter__") else {}

        if isinstance(b, dict):
            b_id = str(b.get("customer_id", b.get("product_id", b.get("order_id", id(b)))))
            b_labels = "Node"
            b_props = b
        else:
            b_id = str(getattr(b, "element_id", id(b)))
            b_labels = list(b.labels)[0] if hasattr(b, "labels") and b.labels else "Node"
            b_props = dict(b) if hasattr(b, "__iter__") else {}

        # Get a display name
        a_name = a_props.get("customer_name", a_props.get("product_name", a_id))
        b_name = b_props.get("customer_name", b_props.get("product_name", b_id))

        nodes[a_id] = {
            "id": a_id,
            "label": str(a_name),
            "type": a_labels,
            "properties": {k: str(v) for k, v in a_props.items()} if isinstance(a_props, dict) else {},
        }
        nodes[b_id] = {
            "id": b_id,
            "label": str(b_name),
            "type": b_labels,
            "properties": {k: str(v) for k, v in b_props.items()} if isinstance(b_props, dict) else {},
        }

        # Process relationship
        rel_type = r[1] if isinstance(r, tuple) else (r.type if hasattr(r, "type") else "RELATED")
        edges.append({
            "source": a_id,
            "target": b_id,
            "relationship": str(rel_type),
            "properties": {},
        })

    return {"nodes": list(nodes.values()), "edges": edges}


def check_connection() -> bool:
    """Check if Neo4j is reachable."""
    try:
        get_graph()
        execute_cypher("RETURN 1 AS test")
        return True
    except Exception:
        return False
