"""
RAG (Retrieval-Augmented Generation) pipeline.
Combines semantic search (Pinecone + HuggingFace embeddings)
with keyword search (Neo4j property matching) for hybrid retrieval.
"""

import logging
from typing import Optional
from sentence_transformers import SentenceTransformer
from backend.config import get_settings
from backend.services import neo4j_service

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Globals ───────────────────────────────────────────────────
_embedding_model: Optional[SentenceTransformer] = None
_pinecone_index = None


def get_embedding_model() -> SentenceTransformer:
    """Get or create the sentence transformer model."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(settings.embedding_model)
        logger.info("✅ Loaded embedding model: %s", settings.embedding_model)
    return _embedding_model


def get_pinecone_index():
    """Get or create the Pinecone index connection."""
    global _pinecone_index
    if _pinecone_index is None:
        try:
            from pinecone import Pinecone
            pc = Pinecone(api_key=settings.pinecone_api_key)

            # Check if index exists, create if not
            existing = [idx.name for idx in pc.list_indexes()]
            if settings.pinecone_index not in existing:
                from pinecone import ServerlessSpec
                pc.create_index(
                    name=settings.pinecone_index,
                    dimension=settings.embedding_dimension,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                )
                logger.info("Created Pinecone index: %s", settings.pinecone_index)

            _pinecone_index = pc.Index(settings.pinecone_index)
            logger.info("✅ Connected to Pinecone index: %s", settings.pinecone_index)
        except Exception as e:
            logger.error("❌ Pinecone connection failed: %s", e)
            _pinecone_index = None
    return _pinecone_index


def embed_text(text: str) -> list[float]:
    """Generate embedding vector for a text string."""
    model = get_embedding_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def index_graph_data():
    """
    Index Neo4j graph node data into Pinecone for semantic search.
    Called once to populate the vector store.
    """
    index = get_pinecone_index()
    if index is None:
        logger.warning("Pinecone not available, skipping indexing")
        return

    # Fetch all nodes with their properties
    nodes_data = []

    # Index Customers
    customers = neo4j_service.execute_cypher(
        "MATCH (c:Customer) RETURN c.customer_id AS id, c.customer_name AS name, "
        "c.segment AS segment, c.region AS region, c.country AS country"
    )
    for c in customers:
        text = f"Customer: {c.get('name', '')} | Segment: {c.get('segment', '')} | Region: {c.get('region', '')} | Country: {c.get('country', '')}"
        nodes_data.append({"id": f"customer_{c['id']}", "text": text, "metadata": {"type": "Customer", **{k: str(v) for k, v in c.items()}}})

    # Index Products
    products = neo4j_service.execute_cypher(
        "MATCH (p:Product) RETURN p.product_id AS id, p.product_name AS name, "
        "p.category AS category, p.supplier AS supplier, p.unit_price AS price"
    )
    for p in products:
        text = f"Product: {p.get('name', '')} | Category: {p.get('category', '')} | Supplier: {p.get('supplier', '')} | Price: {p.get('price', '')}"
        nodes_data.append({"id": f"product_{p['id']}", "text": text, "metadata": {"type": "Product", **{k: str(v) for k, v in p.items()}}})

    # Batch upsert to Pinecone
    if nodes_data:
        model = get_embedding_model()
        batch_size = 100
        for i in range(0, len(nodes_data), batch_size):
            batch = nodes_data[i:i + batch_size]
            texts = [item["text"] for item in batch]
            embeddings = model.encode(texts, normalize_embeddings=True).tolist()

            vectors = [
                {"id": item["id"], "values": emb, "metadata": {**item["metadata"], "text": item["text"]}}
                for item, emb in zip(batch, embeddings)
            ]
            index.upsert(vectors=vectors)

        logger.info("✅ Indexed %d nodes into Pinecone", len(nodes_data))


def semantic_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Perform semantic search: embed query → search Pinecone → return relevant results.
    """
    index = get_pinecone_index()
    if index is None:
        return []

    try:
        query_embedding = embed_text(query)
        results = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)

        return [
            {
                "id": match["id"],
                "score": round(match["score"], 4),
                "text": match.get("metadata", {}).get("text", ""),
                "type": match.get("metadata", {}).get("type", ""),
                "metadata": match.get("metadata", {}),
            }
            for match in results.get("matches", [])
        ]
    except Exception as e:
        logger.error("Semantic search error: %s", e)
        return []


def keyword_search(query: str, limit: int = 5) -> list[dict]:
    """
    Keyword search on Neo4j node properties using CONTAINS filter.
    Searches across customer names, product names, categories, segments.
    """
    keywords = query.lower().split()
    results = []

    for keyword in keywords[:3]:  # Limit to first 3 keywords
        if len(keyword) < 3:
            continue

        cypher = """
        MATCH (n)
        WHERE toLower(n.customer_name) CONTAINS $kw
           OR toLower(n.product_name) CONTAINS $kw
           OR toLower(n.category) CONTAINS $kw
           OR toLower(n.segment) CONTAINS $kw
           OR toLower(n.supplier) CONTAINS $kw
           OR toLower(n.country) CONTAINS $kw
           OR toLower(n.region) CONTAINS $kw
        RETURN labels(n)[0] AS type, properties(n) AS props
        LIMIT $limit
        """
        try:
            matches = neo4j_service.execute_cypher(cypher, {"kw": keyword, "limit": limit})
            for m in matches:
                results.append({
                    "type": m.get("type", "Node"),
                    "properties": {k: str(v) for k, v in m.get("props", {}).items()},
                    "matched_keyword": keyword,
                })
        except Exception as e:
            logger.warning("Keyword search error for '%s': %s", keyword, e)

    return results


def hybrid_search(query: str, top_k: int = 5) -> str:
    """
    Combine semantic + keyword search results into a unified context string.
    This is what gets injected into the LLM prompt.
    """
    context_parts = []

    # Semantic search
    semantic_results = semantic_search(query, top_k=top_k)
    if semantic_results:
        context_parts.append("=== Semantic Search Results ===")
        for r in semantic_results:
            context_parts.append(f"[{r['type']}] {r['text']} (relevance: {r['score']})")

    # Keyword search
    keyword_results = keyword_search(query, limit=top_k)
    if keyword_results:
        context_parts.append("\n=== Keyword Search Results ===")
        for r in keyword_results:
            props_str = ", ".join(f"{k}: {v}" for k, v in r["properties"].items())
            context_parts.append(f"[{r['type']}] {props_str} (matched: {r['matched_keyword']})")

    return "\n".join(context_parts) if context_parts else ""


def check_pinecone_connection() -> bool:
    """Check if Pinecone is reachable."""
    try:
        index = get_pinecone_index()
        return index is not None
    except Exception:
        return False
