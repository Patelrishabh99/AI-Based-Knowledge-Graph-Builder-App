"""
Vector DB Benchmark Service.
Runs identical queries against FAISS and Pinecone, measures performance,
and provides a detailed comparison with recommendation.
"""

import time
import logging
from backend.services import rag_service
from backend.services import faiss_service

logger = logging.getLogger(__name__)


# ── Static comparison data ────────────────────────────────────
COMPARISON_PROPERTIES = {
    "faiss": {
        "name": "FAISS",
        "full_name": "Facebook AI Similarity Search",
        "hosting": "Local / Self-hosted",
        "cost": "Free & Open Source",
        "scalability": "Single machine (RAM-bound)",
        "latency": "Sub-millisecond (in-memory)",
        "max_vectors": "Billions (with enough RAM)",
        "persistence": "File-based (manual save/load)",
        "filtering": "No native metadata filtering",
        "managed_service": "No",
        "real_time_updates": "Requires index rebuild",
        "multi_tenancy": "Not built-in",
        "cloud_native": "No",
        "index_types": "Flat, IVF, HNSW, PQ, LSH",
        "best_for": "Offline search, prototyping, cost-sensitive apps, edge deployment",
        "language": "C++ with Python bindings",
        "maintained_by": "Meta AI Research",
    },
    "pinecone": {
        "name": "Pinecone",
        "full_name": "Pinecone Vector Database",
        "hosting": "Fully managed cloud (AWS/GCP/Azure)",
        "cost": "Freemium ($0–$70+/mo based on usage)",
        "scalability": "Horizontal auto-scaling, serverless",
        "latency": "~10–50ms (network + compute)",
        "max_vectors": "Unlimited (serverless tier)",
        "persistence": "Built-in, durable cloud storage",
        "filtering": "Rich metadata filtering with namespaces",
        "managed_service": "Yes — zero ops",
        "real_time_updates": "Real-time upsert/delete",
        "multi_tenancy": "Built-in via namespaces",
        "cloud_native": "Yes",
        "index_types": "Proprietary optimized index",
        "best_for": "Production apps, real-time search, enterprise, multi-user",
        "language": "API-based (REST/gRPC)",
        "maintained_by": "Pinecone Inc.",
    },
}


def get_comparison_properties() -> dict:
    """Return the static comparison properties for FAISS vs Pinecone."""
    return COMPARISON_PROPERTIES


def run_benchmark(query: str, top_k: int = 5) -> dict:
    """
    Run the same query against both FAISS and Pinecone, measure performance.
    Returns detailed results for side-by-side comparison.
    """
    results = {
        "query": query,
        "top_k": top_k,
        "faiss": {"available": False, "results": [], "latency_ms": 0, "error": None},
        "pinecone": {"available": False, "results": [], "latency_ms": 0, "error": None},
        "recommendation": {},
    }

    # ── FAISS search ──────────────────────────────────────
    try:
        faiss_results, faiss_latency = faiss_service.semantic_search(query, top_k=top_k)
        results["faiss"] = {
            "available": len(faiss_results) > 0,
            "results": faiss_results,
            "latency_ms": faiss_latency,
            "result_count": len(faiss_results),
            "error": None,
        }
    except Exception as e:
        results["faiss"]["error"] = str(e)
        logger.warning("FAISS benchmark error: %s", e)

    # ── Pinecone search ───────────────────────────────────
    try:
        start = time.time()
        pinecone_results = rag_service.semantic_search(query, top_k=top_k)
        pinecone_latency = (time.time() - start) * 1000

        results["pinecone"] = {
            "available": len(pinecone_results) > 0,
            "results": pinecone_results,
            "latency_ms": round(pinecone_latency, 2),
            "result_count": len(pinecone_results),
            "error": None,
        }
    except Exception as e:
        results["pinecone"]["error"] = str(e)
        logger.warning("Pinecone benchmark error: %s", e)

    # ── Generate recommendation ───────────────────────────
    results["recommendation"] = _generate_recommendation(results)

    return results


def _generate_recommendation(results: dict) -> dict:
    """
    Generate a recommendation based on benchmark results and use case analysis.
    """
    faiss_data = results.get("faiss", {})
    pinecone_data = results.get("pinecone", {})

    faiss_latency = faiss_data.get("latency_ms", 0)
    pinecone_latency = pinecone_data.get("latency_ms", 0)

    # Speed comparison
    speed_winner = "faiss" if faiss_latency < pinecone_latency and faiss_latency > 0 else "pinecone"

    return {
        "production_choice": "Pinecone",
        "speed_winner": "FAISS" if speed_winner == "faiss" else "Pinecone",
        "faiss_latency_ms": faiss_latency,
        "pinecone_latency_ms": pinecone_latency,
        "reasoning": [
            "🏆 **Pinecone is recommended for production** in this enterprise app.",
            "✅ Pinecone offers managed infrastructure with zero-ops maintenance.",
            "✅ Pinecone supports real-time updates, metadata filtering, and multi-tenancy.",
            "✅ Pinecone scales horizontally without code changes.",
            "✅ Pinecone provides built-in high availability and durability.",
            "",
            "📊 **FAISS excels at**:",
            "⚡ Sub-millisecond local queries (no network latency).",
            "💰 Zero cost — fully open source.",
            "🔒 Data stays on your machine (privacy-sensitive use cases).",
            "🧪 Great for prototyping and offline experimentation.",
        ],
        "our_project_uses": "Pinecone",
        "why": (
            "This project uses Pinecone because it's a cloud-deployed enterprise application "
            "that needs real-time semantic search with horizontal scalability, metadata filtering, "
            "and zero operational overhead. The FAISS implementation is provided for benchmarking "
            "and as an alternative for local/offline development."
        ),
    }


def get_faiss_stats() -> dict:
    """Get current FAISS index statistics."""
    return faiss_service.get_index_stats()


def get_pinecone_stats() -> dict:
    """Get current Pinecone index statistics."""
    try:
        index = rag_service.get_pinecone_index()
        if index is None:
            return {"connected": False}
        stats = index.describe_index_stats()

        # Convert namespace objects to plain dicts (NamespaceSummary is not JSON-serializable)
        raw_namespaces = stats.get("namespaces", {})
        namespaces = {}
        for ns_key, ns_val in raw_namespaces.items():
            try:
                namespaces[str(ns_key)] = {"vector_count": getattr(ns_val, "vector_count", str(ns_val))}
            except Exception:
                namespaces[str(ns_key)] = str(ns_val)

        return {
            "connected": True,
            "total_vectors": int(stats.get("total_vector_count", 0)),
            "dimension": int(stats.get("dimension", 0)),
            "namespaces": namespaces,
        }
    except Exception as e:
        logger.warning("Pinecone stats error: %s", e)
        return {"connected": False, "error": str(e)}
