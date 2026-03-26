"""
Data Loading Script.
Loads CSV data into Neo4j and indexes graph nodes into Pinecone.
Run this once to set up the database and vector store.

Usage:
    python -m scripts.load_data
"""

import os
import sys
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from backend.services import neo4j_service, rag_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def load_csv_data():
    """Load customer, product, and order data from CSV into Neo4j."""
    logger.info("📦 Loading data into Neo4j...")

    # ── Customers ─────────────────────────────────────────
    customer_query = """
    LOAD CSV WITH HEADERS FROM
    'https://raw.githubusercontent.com/Patelrishabh99/AI-Based-Knowledge-Graph-Builder/refs/heads/main/dim_customer.csv' AS row
    WITH row WHERE row.customer_id IS NOT NULL
    MERGE (c:Customer {customer_id: toInteger(row.customer_id)})
    SET c.customer_name = row.customer_name,
        c.segment       = row.segment,
        c.region        = row.region,
        c.country       = row.country
    """
    neo4j_service.execute_cypher(customer_query)
    logger.info("✅ Customers loaded")

    # ── Products ──────────────────────────────────────────
    product_query = """
    LOAD CSV WITH HEADERS FROM
    'https://raw.githubusercontent.com/Patelrishabh99/AI-Based-Knowledge-Graph-Builder/refs/heads/main/dim_product.csv' AS row
    WITH row WHERE row.product_id IS NOT NULL
    MERGE (p:Product {product_id: toInteger(row.product_id)})
    SET p.product_name = row.product_name,
        p.category     = row.category,
        p.unit_price   = toFloat(row.unit_price),
        p.supplier     = row.supplier
    """
    neo4j_service.execute_cypher(product_query)
    logger.info("✅ Products loaded")

    # ── Orders + Relationships ────────────────────────────
    order_query = """
    LOAD CSV WITH HEADERS FROM
    'https://raw.githubusercontent.com/Patelrishabh99/AI-Based-Knowledge-Graph-Builder/refs/heads/main/fact_order.csv' AS row
    WITH row
    WHERE row.order_id IS NOT NULL
      AND row.customer_id IS NOT NULL
      AND row.product_id IS NOT NULL
    MERGE (o:Order {order_id: toInteger(row.order_id)})
    SET o.order_date   = date(row.order_date),
        o.quantity     = toInteger(row.quantity),
        o.unit_price   = toFloat(row.unit_price),
        o.sales_amount = toFloat(row.sales_amount),
        o.order_year   = toInteger(row.order_year),
        o.order_month  = row.order_month
    WITH row, o
    MATCH (c:Customer {customer_id: toInteger(row.customer_id)})
    MATCH (p:Product  {product_id: toInteger(row.product_id)})
    MERGE (c)-[:PLACED]->(o)
    MERGE (o)-[:CONTAINS]->(p)
    """
    neo4j_service.execute_cypher(order_query)
    logger.info("✅ Orders and relationships loaded")


def index_to_pinecone():
    """Index graph node data into Pinecone for semantic search."""
    logger.info("🔍 Indexing graph data into Pinecone...")
    try:
        rag_service.index_graph_data()
        logger.info("✅ Pinecone indexing complete")
    except Exception as e:
        logger.warning("⚠️ Pinecone indexing failed (non-critical): %s", e)


def print_stats():
    """Print graph statistics."""
    stats = neo4j_service.get_graph_stats()
    logger.info("📊 Graph Statistics:")
    logger.info("   Nodes: %d", stats["total_nodes"])
    logger.info("   Relationships: %d", stats["total_relationships"])
    logger.info("   Labels: %s", stats["node_labels"])
    logger.info("   Relationship Types: %s", stats["relationship_types"])


if __name__ == "__main__":
    print("=" * 60)
    print("  AI Graph Builder — Data Loader")
    print("=" * 60)

    # Step 1: Load CSV data
    load_csv_data()

    # Step 2: Print stats
    print_stats()

    # Step 3: Index into Pinecone
    index_to_pinecone()

    print("\n✅ Data loading complete!")
