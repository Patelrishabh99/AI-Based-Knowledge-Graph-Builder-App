"""
FAISS Vector Store Service.
Local, in-memory vector search using Facebook AI Similarity Search.
Mirrors the Pinecone service for side-by-side comparison.
"""

import os
import logging
import time
from typing import Optional
from sentence_transformers import SentenceTransformer
from backend.config import get_settings
from backend.services import neo4j_service

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Globals ───────────────────────────────────────────────────
_faiss_index = None
_faiss_metadata: list[dict] = []
_embedding_model: Optional[SentenceTransformer] = None

FAISS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "faiss_index")


def _get_embedding_model() -> SentenceTransformer:
    """Get or create the sentence transformer model (shared with Pinecone)."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(settings.embedding_model)
        logger.info("✅ FAISS: Loaded embedding model: %s", settings.embedding_model)
    return _embedding_model


def _embed_text(text: str) -> list[float]:
    """Generate embedding vector for a text string."""
    model = _get_embedding_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def _embed_batch(texts: list[str]):
    """Generate embeddings for a batch of texts. Returns numpy array."""
    model = _get_embedding_model()
    return model.encode(texts, normalize_embeddings=True)


def index_graph_data() -> dict:
    """
    Index Neo4j graph node data into a local FAISS index.
    Returns stats about the indexing operation.
    """
    global _faiss_index, _faiss_metadata

    try:
        import faiss
        import numpy as np
    except ImportError:
        logger.error("❌ faiss-cpu is not installed. Run: pip install faiss-cpu")
        return {"status": "error", "message": "faiss-cpu not installed"}

    start = time.time()
    nodes_data = []

    # ── Fetch Customer nodes ──────────────────────────────
    try:
        customers = neo4j_service.execute_cypher(
            "MATCH (c:Customer) RETURN c.customer_id AS id, c.customer_name AS name, "
            "c.segment AS segment, c.region AS region, c.country AS country"
        )
        for c in customers:
            text = (
                f"Customer: {c.get('name', '')} | Segment: {c.get('segment', '')} "
                f"| Region: {c.get('region', '')} | Country: {c.get('country', '')}"
            )
            nodes_data.append({
                "id": f"customer_{c['id']}",
                "text": text,
                "metadata": {"type": "Customer", **{k: str(v) for k, v in c.items()}},
            })
    except Exception as e:
        logger.warning("FAISS index: could not fetch customers: %s", e)

    # ── Fetch Product nodes ───────────────────────────────
    try:
        products = neo4j_service.execute_cypher(
            "MATCH (p:Product) RETURN p.product_id AS id, p.product_name AS name, "
            "p.category AS category, p.supplier AS supplier, p.unit_price AS price"
        )
        for p in products:
            text = (
                f"Product: {p.get('name', '')} | Category: {p.get('category', '')} "
                f"| Supplier: {p.get('supplier', '')} | Price: {p.get('price', '')}"
            )
            nodes_data.append({
                "id": f"product_{p['id']}",
                "text": text,
                "metadata": {"type": "Product", **{k: str(v) for k, v in p.items()}},
            })
    except Exception as e:
        logger.warning("FAISS index: could not fetch products: %s", e)

    if not nodes_data:
        return {"status": "warning", "message": "No data to index", "count": 0}

    # ── Build FAISS index ─────────────────────────────────
    texts = [item["text"] for item in nodes_data]
    embeddings = _embed_batch(texts).astype(np.float32)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner Product (cosine with normalized vectors)
    index.add(embeddings)

    _faiss_index = index
    _faiss_metadata = nodes_data

    # ── Save to disk ──────────────────────────────────────
    os.makedirs(FAISS_DIR, exist_ok=True)
    faiss.write_index(index, os.path.join(FAISS_DIR, "index.faiss"))

    import json
    with open(os.path.join(FAISS_DIR, "metadata.json"), "w") as f:
        json.dump(nodes_data, f)

    elapsed = (time.time() - start) * 1000
    logger.info("✅ FAISS: Indexed %d nodes in %.0fms", len(nodes_data), elapsed)

    return {
        "status": "success",
        "count": len(nodes_data),
        "dimension": dimension,
        "index_time_ms": round(elapsed, 2),
    }


def load_index() -> bool:
    """Load a saved FAISS index from disk."""
    global _faiss_index, _faiss_metadata
    try:
        import faiss
        import json

        index_path = os.path.join(FAISS_DIR, "index.faiss")
        meta_path = os.path.join(FAISS_DIR, "metadata.json")

        if not os.path.exists(index_path):
            return False

        _faiss_index = faiss.read_index(index_path)
        with open(meta_path, "r") as f:
            _faiss_metadata = json.load(f)

        logger.info("✅ FAISS: Loaded index with %d vectors", _faiss_index.ntotal)
        return True
    except Exception as e:
        logger.warning("Could not load FAISS index: %s", e)
        return False


def semantic_search(query: str, top_k: int = 5) -> tuple[list[dict], float]:
    """
    Perform semantic search on the FAISS index.
    Returns (results, latency_ms).
    """
    global _faiss_index, _faiss_metadata

    if _faiss_index is None:
        load_index()

    if _faiss_index is None or not _faiss_metadata:
        return [], 0.0

    try:
        import numpy as np
        start = time.time()

        query_vec = np.array([_embed_text(query)], dtype=np.float32)
        scores, indices = _faiss_index.search(query_vec, min(top_k, _faiss_index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(_faiss_metadata):
                continue
            meta = _faiss_metadata[idx]
            results.append({
                "id": meta["id"],
                "score": round(float(score), 4),
                "text": meta["text"],
                "type": meta["metadata"].get("type", ""),
                "metadata": meta["metadata"],
            })

        latency = (time.time() - start) * 1000
        return results, round(latency, 2)

    except Exception as e:
        logger.error("FAISS search error: %s", e)
        return [], 0.0


def check_faiss_connection() -> bool:
    """Check if FAISS index is loaded."""
    global _faiss_index
    if _faiss_index is not None:
        return True
    return load_index()


def get_index_stats() -> dict:
    """Get FAISS index statistics."""
    global _faiss_index, _faiss_metadata
    if _faiss_index is None:
        load_index()

    if _faiss_index is None:
        return {"loaded": False, "total_vectors": 0}

    return {
        "loaded": True,
        "total_vectors": _faiss_index.ntotal,
        "dimension": _faiss_index.d,
        "index_type": "IndexFlatIP (Cosine)",
        "metadata_count": len(_faiss_metadata),
    }
