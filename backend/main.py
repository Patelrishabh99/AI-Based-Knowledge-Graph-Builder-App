"""
FastAPI Application — AI-Based Graph Builder for Enterprise Intelligence.
Provides REST API endpoints for query processing, graph exploration,
multi-LLM comparison, dashboard metrics, and session management.
"""

import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.config import get_settings
from backend.middleware import limiter, verify_api_key
from backend.models.schemas import (
    QueryRequest, QueryResponse, CompareRequest, CompareResponse,
    GraphExploreRequest, GraphData, DashboardMetrics,
    HealthResponse, ModelComparison,
    BenchmarkRequest, BenchmarkResponse,
    NotifyRequest, NotifyResponse,
)
from backend.services import (
    neo4j_service, llm_service, rag_service,
    cypher_generator, query_intelligence,
    session_service, metrics_service,
)
from backend.services import faiss_service, vectordb_benchmark, notification_service

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)
settings = get_settings()


# ── Lifespan ──────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🚀 Starting AI Graph Builder API...")
    # Warm up connections
    try:
        neo4j_service.get_graph()
        logger.info("✅ Neo4j connected")
    except Exception as e:
        logger.warning("⚠️ Neo4j not available at startup: %s", e)
    yield
    logger.info("🛑 Shutting down API...")


# ── App ───────────────────────────────────────────────────────
app = FastAPI(
    title="AI Graph Builder API",
    description="Enterprise Intelligence powered by Knowledge Graphs + RAG + Multi-LLM",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════════════════════
#  ENDPOINTS
# ══════════════════════════════════════════════════════════════

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        neo4j_connected=neo4j_service.check_connection(),
        pinecone_connected=rag_service.check_pinecone_connection(),
        faiss_loaded=faiss_service.check_faiss_connection(),
    )


@app.post("/api/query")
@limiter.limit("30/minute")
async def process_query(request: Request, body: QueryRequest):
    """
    Main query endpoint.
    1. Analyze query intent
    2. Generate Cypher and fetch graph data
    3. Optionally enrich with RAG (semantic + keyword search)
    4. Generate AI response
    """
    await verify_api_key(request)
    start = time.time()

    try:
        # Step 1: Query Intelligence
        analysis = query_intelligence.analyze_query(body.query)
        logger.info("Query analysis: intent=%s, entities=%s", analysis["intent"], analysis["entities"])

        # Step 2: Generate Cypher & get graph results
        cypher_result = cypher_generator.generate_cypher(body.query, model_name=body.model)
        cypher_text = cypher_result.get("cypher", "")
        raw_results = cypher_result.get("raw_results", [])
        chain_answer = cypher_result.get("answer", "")

        # Step 3: RAG enrichment
        rag_context = ""
        sources = []
        if body.use_rag:
            try:
                rag_context = rag_service.hybrid_search(body.query)
                if rag_context:
                    sources = [line for line in rag_context.split("\n") if line.strip() and not line.startswith("===")]
            except Exception as rag_err:
                logger.warning("RAG search error (non-fatal): %s", rag_err)

        # Step 4: Build full context and generate response
        full_context = ""
        if raw_results:
            full_context += f"Graph Query Results:\n{raw_results}\n\n"
        if rag_context:
            full_context += f"Additional Context:\n{rag_context}\n"

        # Session context
        if body.session_id:
            session_context = session_service.get_session_context(body.session_id)
            if session_context:
                full_context = session_context + "\n\n" + full_context

        # Generate final answer (use chain answer as fallback)
        model = body.model or settings.default_model
        answer = chain_answer
        token_usage = {}

        if full_context:
            try:
                llm_result = llm_service.generate_response(
                    query=body.query,
                    context=full_context,
                    model_name=model,
                )
                answer = llm_result.get("answer", chain_answer) or chain_answer
                token_usage = llm_result.get("token_usage", {})
            except Exception as llm_err:
                logger.warning("LLM enhancement error (using chain answer): %s", llm_err)

        latency_ms = (time.time() - start) * 1000

        # Record metrics
        metrics_service.record_query(body.query, latency_ms, model)

        # Store in session
        if body.session_id:
            session_service.add_query_to_session(
                body.session_id, body.query, answer,
                cypher=cypher_text, model=model,
            )

        # Return plain dict (avoid Pydantic validation issues with nested models)
        return {
            "query": body.query,
            "answer": answer,
            "cypher_query": cypher_text,
            "raw_results": raw_results[:20] if isinstance(raw_results, list) else [],
            "sources": sources[:5],
            "model_used": model,
            "latency_ms": round(latency_ms, 2),
            "token_usage": token_usage,
            "intent": analysis.get("intent", ""),
            "entities": [e.get("entity", "") for e in analysis.get("entities", [])],
        }
    except Exception as e:
        latency_ms = (time.time() - start) * 1000
        metrics_service.record_query(body.query, latency_ms, body.model or "unknown", success=False)
        logger.error("Query processing error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compare", response_model=CompareResponse)
@limiter.limit("10/minute")
async def compare_models(request: Request, body: CompareRequest):
    """Run the same query across multiple LLMs and compare results."""
    await verify_api_key(request)

    try:
        # Get graph context first
        cypher_result = cypher_generator.generate_cypher(body.query)
        context = str(cypher_result.get("raw_results", ""))

        # Add RAG context
        rag_context = rag_service.hybrid_search(body.query)
        if rag_context:
            context += f"\n\n{rag_context}"

        # Compare models
        results = llm_service.compare_models(
            query=body.query,
            context=context,
            models=body.models,
        )

        # Record metrics for each model
        for r in results:
            metrics_service.record_query(body.query, r["latency_ms"], r["model"], success="error" not in r)

        return CompareResponse(
            query=body.query,
            results=[
                ModelComparison(
                    model=r["model"],
                    answer=r["answer"],
                    latency_ms=r["latency_ms"],
                    token_usage=r.get("token_usage", {}),
                    error=r.get("error"),
                )
                for r in results
            ],
        )
    except Exception as e:
        logger.error("Comparison error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/graph", response_model=GraphData)
@limiter.limit("30/minute")
async def explore_graph(request: Request, body: GraphExploreRequest):
    """Fetch graph data for 3D visualization."""
    await verify_api_key(request)

    try:
        data = neo4j_service.get_graph_visualization_data(
            node_type=body.node_type,
            relationship_type=body.relationship_type,
            limit=body.limit,
        )
        return GraphData(
            nodes=[
                {"id": n["id"], "label": n["label"], "type": n["type"], "properties": n["properties"]}
                for n in data["nodes"]
            ],
            edges=[
                {"source": e["source"], "target": e["target"], "relationship": e["relationship"], "properties": e["properties"]}
                for e in data["edges"]
            ],
        )
    except Exception as e:
        logger.error("Graph exploration error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard", response_model=DashboardMetrics)
async def get_dashboard():
    """Get enterprise dashboard metrics."""
    try:
        graph_stats = neo4j_service.get_graph_stats()
        return metrics_service.get_dashboard_metrics(graph_stats=graph_stats)
    except Exception as e:
        logger.error("Dashboard error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions")
async def create_session():
    """Create a new chat session."""
    session_id = session_service.create_session()
    return {"session_id": session_id}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session history."""
    return session_service.get_session(session_id)


@app.get("/api/sessions")
async def list_sessions():
    """List all active sessions."""
    return session_service.get_all_sessions()


@app.get("/api/schema")
async def get_graph_schema():
    """Get the Neo4j graph schema."""
    return {"schema": neo4j_service.get_schema()}


@app.get("/api/models")
async def list_models():
    """List available LLM models."""
    return {"models": llm_service.get_available_models(), "default": settings.default_model}


@app.post("/api/index")
async def index_data(request: Request):
    """Index Neo4j graph data into Pinecone for semantic search."""
    await verify_api_key(request)
    try:
        rag_service.index_graph_data()
        return {"status": "success", "message": "Graph data indexed into Pinecone"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════
#  VECTOR DB BENCHMARK ENDPOINTS
# ══════════════════════════════════════════════════════════════

@app.post("/api/vectordb/benchmark")
@limiter.limit("10/minute")
async def benchmark_vectordbs(request: Request, body: BenchmarkRequest):
    """Run FAISS vs Pinecone benchmark on a query."""
    await verify_api_key(request)
    try:
        result = vectordb_benchmark.run_benchmark(body.query, top_k=body.top_k)
        return result
    except Exception as e:
        logger.error("Benchmark error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vectordb/index-faiss")
async def index_faiss(request: Request):
    """Index Neo4j graph data into FAISS for local semantic search."""
    await verify_api_key(request)
    try:
        result = faiss_service.index_graph_data()
        return result
    except Exception as e:
        logger.error("FAISS indexing error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vectordb/comparison")
async def get_vectordb_comparison():
    """Get static FAISS vs Pinecone property comparison."""
    return {
        "properties": vectordb_benchmark.get_comparison_properties(),
        "faiss_stats": vectordb_benchmark.get_faiss_stats(),
        "pinecone_stats": vectordb_benchmark.get_pinecone_stats(),
    }


# ══════════════════════════════════════════════════════════════
#  NOTIFICATION ENDPOINTS
# ══════════════════════════════════════════════════════════════

@app.post("/api/notify", response_model=NotifyResponse)
async def send_notification(body: NotifyRequest):
    """Generate a WhatsApp share link for query activity notification."""
    try:
        result = notification_service.format_query_notification(
            query=body.query,
            model=body.model,
            answer_summary=body.answer_summary,
            response_type=body.response_type,
            latency_ms=body.latency_ms,
            intent=body.intent,
        )
        return NotifyResponse(
            whatsapp_url=result["whatsapp_url"],
            message=result["message"],
            timestamp=result["timestamp"],
            group_link=notification_service.get_group_link(),
        )
    except Exception as e:
        logger.error("Notification error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
