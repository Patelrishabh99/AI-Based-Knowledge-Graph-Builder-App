"""
Pydantic models (schemas) for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── Request Models ─────────────────────────────────────────────

class QueryRequest(BaseModel):
    """Natural language query request."""
    query: str = Field(..., min_length=1, max_length=2000, description="Natural language query")
    session_id: Optional[str] = Field(None, description="Session ID for context-aware follow-ups")
    model: Optional[str] = Field(None, description="Specific LLM model to use")
    use_rag: bool = Field(True, description="Whether to use RAG pipeline")


class CompareRequest(BaseModel):
    """Multi-LLM comparison request."""
    query: str = Field(..., min_length=1, max_length=2000)
    models: Optional[list[str]] = Field(None, description="Models to compare; defaults to all")


class GraphExploreRequest(BaseModel):
    """Graph exploration request."""
    node_type: Optional[str] = Field(None, description="Filter by node label")
    relationship_type: Optional[str] = Field(None, description="Filter by relationship type")
    limit: int = Field(100, ge=1, le=500, description="Max nodes to return")


# ── Response Models ────────────────────────────────────────────

class CypherResult(BaseModel):
    """Generated Cypher query and its results."""
    cypher: str
    raw_results: list[dict]


class QueryResponse(BaseModel):
    """Full query response with AI answer, Cypher, and metadata."""
    query: str
    answer: str
    cypher: Optional[CypherResult] = None
    sources: list[str] = []
    model_used: str = ""
    latency_ms: float = 0.0
    token_usage: dict = {}
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ModelComparison(BaseModel):
    """Single model's response in a comparison."""
    model: str
    answer: str
    latency_ms: float
    token_usage: dict = {}
    error: Optional[str] = None


class CompareResponse(BaseModel):
    """Multi-model comparison results."""
    query: str
    results: list[ModelComparison]


class GraphNode(BaseModel):
    """Node for graph visualization."""
    id: str
    label: str
    type: str
    properties: dict = {}


class GraphEdge(BaseModel):
    """Edge for graph visualization."""
    source: str
    target: str
    relationship: str
    properties: dict = {}


class GraphData(BaseModel):
    """Graph data for 3D visualization."""
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class DashboardMetrics(BaseModel):
    """Enterprise dashboard metrics."""
    total_queries: int = 0
    avg_response_time_ms: float = 0.0
    model_usage: dict = {}
    queries_over_time: list[dict] = []
    graph_stats: dict = {}
    top_queries: list[dict] = []


class SessionData(BaseModel):
    """Session history data."""
    session_id: str
    queries: list[dict] = []
    created_at: str = ""


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    neo4j_connected: bool = False
    pinecone_connected: bool = False
    faiss_loaded: bool = False
    version: str = "1.0.0"


# ── Vector DB Benchmark ───────────────────────────────────────

class BenchmarkRequest(BaseModel):
    """Vector DB benchmark request."""
    query: str = Field(..., min_length=1, max_length=2000, description="Query to benchmark")
    top_k: int = Field(5, ge=1, le=50, description="Number of results to return")


class BenchmarkResponse(BaseModel):
    """Vector DB benchmark results."""
    query: str
    top_k: int
    faiss: dict = {}
    pinecone: dict = {}
    recommendation: dict = {}


# ── Notification ──────────────────────────────────────────────

class NotifyRequest(BaseModel):
    """Query notification request."""
    query: str = Field(..., description="The query that was asked")
    model: str = Field("", description="Model used")
    answer_summary: str = Field("", description="Summary of the answer")
    response_type: str = Field("text", description="Type of response")
    latency_ms: float = Field(0, description="Response latency in ms")
    intent: str = Field("", description="Detected query intent")


class NotifyResponse(BaseModel):
    """Notification response with share link."""
    whatsapp_url: str
    message: str
    timestamp: str
    group_link: str = ""
