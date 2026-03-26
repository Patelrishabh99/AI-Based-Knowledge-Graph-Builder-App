"""
Metrics tracking service for the Enterprise Dashboard.
Tracks query counts, response times, model usage, and system performance.
"""

import time
import logging
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

# ── In-memory metrics store ───────────────────────────────────
_metrics = {
    "total_queries": 0,
    "response_times": [],       # list of (timestamp, latency_ms)
    "model_usage": defaultdict(int),  # model_name -> count
    "query_log": [],            # list of (timestamp, query, latency_ms, model)
    "errors": 0,
}


def record_query(query: str, latency_ms: float, model: str, success: bool = True):
    """Record a query execution for metrics."""
    _metrics["total_queries"] += 1
    _metrics["response_times"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "latency_ms": latency_ms,
    })
    _metrics["model_usage"][model] += 1
    _metrics["query_log"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "query": query[:100],  # truncate
        "latency_ms": latency_ms,
        "model": model,
        "success": success,
    })

    if not success:
        _metrics["errors"] += 1

    # Keep only last 1000 entries
    if len(_metrics["response_times"]) > 1000:
        _metrics["response_times"] = _metrics["response_times"][-1000:]
    if len(_metrics["query_log"]) > 1000:
        _metrics["query_log"] = _metrics["query_log"][-1000:]


def get_dashboard_metrics(graph_stats: dict = None) -> dict:
    """
    Compute dashboard metrics for display.
    Returns aggregated statistics for charts and KPI cards.
    """
    # Average response time
    times = [r["latency_ms"] for r in _metrics["response_times"]]
    avg_time = sum(times) / len(times) if times else 0

    # Model usage breakdown
    model_usage = dict(_metrics["model_usage"])

    # Queries over time (last 20 entries for chart)
    queries_over_time = _metrics["query_log"][-20:]

    # Top queries (most recent unique)
    seen = set()
    top_queries = []
    for q in reversed(_metrics["query_log"]):
        if q["query"] not in seen and len(top_queries) < 10:
            top_queries.append(q)
            seen.add(q["query"])

    return {
        "total_queries": _metrics["total_queries"],
        "avg_response_time_ms": round(avg_time, 2),
        "model_usage": model_usage,
        "queries_over_time": queries_over_time,
        "graph_stats": graph_stats or {},
        "top_queries": top_queries,
        "error_count": _metrics["errors"],
        "success_rate": round(
            ((_metrics["total_queries"] - _metrics["errors"]) / _metrics["total_queries"] * 100)
            if _metrics["total_queries"] > 0 else 100,
            1,
        ),
    }


def get_response_time_series() -> list[dict]:
    """Get response time data for time-series chart."""
    return _metrics["response_times"][-50:]


def reset_metrics():
    """Reset all metrics (for testing)."""
    _metrics["total_queries"] = 0
    _metrics["response_times"] = []
    _metrics["model_usage"] = defaultdict(int)
    _metrics["query_log"] = []
    _metrics["errors"] = 0
