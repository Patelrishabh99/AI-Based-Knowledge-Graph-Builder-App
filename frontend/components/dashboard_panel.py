"""
Enterprise Dashboard Panel — KPI cards and Plotly charts.
Displays query metrics, model usage, response times, and graph statistics.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from frontend.utils import api_get
from frontend.styles import render_kpi_card


def create_latency_chart(queries_over_time: list) -> go.Figure:
    """Create response time line chart."""
    if not queries_over_time:
        fig = go.Figure()
        fig.update_layout(title="No data yet", paper_bgcolor="#0a0e1a", plot_bgcolor="#111827")
        return fig

    timestamps = [q.get("timestamp", "")[:19] for q in queries_over_time]
    latencies = [q.get("latency_ms", 0) for q in queries_over_time]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=timestamps, y=latencies,
        mode="lines+markers",
        line=dict(color="#6366f1", width=2),
        marker=dict(size=6, color="#8b5cf6"),
        fill="tozeroy",
        fillcolor="rgba(99, 102, 241, 0.1)",
        name="Latency (ms)",
    ))

    fig.update_layout(
        title=dict(text="Response Time Over Queries", font=dict(color="#f1f5f9", size=14)),
        xaxis=dict(title="", showgrid=False, color="#64748b", tickangle=-45),
        yaxis=dict(title="Latency (ms)", showgrid=True, gridcolor="rgba(99,102,241,0.1)", color="#64748b"),
        paper_bgcolor="#0a0e1a",
        plot_bgcolor="#111827",
        height=300,
        margin=dict(l=50, r=20, t=50, b=80),
    )
    return fig


def create_model_usage_chart(model_usage: dict) -> go.Figure:
    """Create model usage pie chart."""
    if not model_usage:
        fig = go.Figure()
        fig.update_layout(title="No model usage data", paper_bgcolor="#0a0e1a", plot_bgcolor="#111827")
        return fig

    models = list(model_usage.keys())
    counts = list(model_usage.values())
    colors = ["#6366f1", "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#f43f5e"]

    fig = go.Figure(data=[go.Pie(
        labels=models,
        values=counts,
        marker=dict(colors=colors[:len(models)], line=dict(color="#0a0e1a", width=2)),
        textinfo="label+percent",
        textfont=dict(color="#f1f5f9", size=11),
        hole=0.4,
    )])

    fig.update_layout(
        title=dict(text="Model Usage Distribution", font=dict(color="#f1f5f9", size=14)),
        paper_bgcolor="#0a0e1a",
        plot_bgcolor="#111827",
        height=300,
        showlegend=False,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def create_graph_stats_chart(graph_stats: dict) -> go.Figure:
    """Create graph statistics bar chart."""
    labels = graph_stats.get("node_labels", [])
    if not labels:
        fig = go.Figure()
        fig.update_layout(title="No graph stats", paper_bgcolor="#0a0e1a", plot_bgcolor="#111827")
        return fig

    colors = {"Customer": "#6366f1", "Product": "#10b981", "Order": "#f59e0b"}

    fig = go.Figure(data=[go.Bar(
        x=labels,
        y=[graph_stats.get("total_nodes", 0) // len(labels)] * len(labels),
        marker=dict(
            color=[colors.get(l, "#94a3b8") for l in labels],
            line=dict(width=0),
        ),
        text=labels,
        textposition="auto",
        textfont=dict(color="#f1f5f9"),
    )])

    fig.update_layout(
        title=dict(text="Node Distribution by Type", font=dict(color="#f1f5f9", size=14)),
        xaxis=dict(showgrid=False, color="#64748b"),
        yaxis=dict(showgrid=True, gridcolor="rgba(99,102,241,0.1)", color="#64748b", title="Count"),
        paper_bgcolor="#0a0e1a",
        plot_bgcolor="#111827",
        height=300,
        margin=dict(l=50, r=20, t=50, b=40),
    )
    return fig


def render_dashboard_panel():
    """Render the enterprise dashboard with KPIs and charts."""

    st.markdown("### 📊 Enterprise Intelligence Dashboard")

    # Fetch metrics
    if st.button("🔄 Refresh Dashboard", key="refresh_dashboard"):
        st.session_state["dashboard_refresh"] = True

    metrics = api_get("/api/dashboard")

    if "error" in metrics:
        st.warning(f"Dashboard unavailable: {metrics['error']}")
        st.info("Start the backend server first: `uvicorn backend.main:app --reload`")
        return

    # ── KPI Cards ─────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(render_kpi_card(
            "Total Queries", str(metrics.get("total_queries", 0)), "🔍"
        ), unsafe_allow_html=True)

    with col2:
        avg_time = metrics.get("avg_response_time_ms", 0)
        st.markdown(render_kpi_card(
            "Avg Response Time", f"{avg_time:.0f}ms", "⚡"
        ), unsafe_allow_html=True)

    with col3:
        success_rate = metrics.get("success_rate", 100)
        st.markdown(render_kpi_card(
            "Success Rate", f"{success_rate}%", "✅"
        ), unsafe_allow_html=True)

    with col4:
        graph_stats = metrics.get("graph_stats", {})
        total_nodes = graph_stats.get("total_nodes", 0)
        st.markdown(render_kpi_card(
            "Graph Nodes", str(total_nodes), "🌐"
        ), unsafe_allow_html=True)

    st.markdown("---")

    # ── Charts ────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        latency_fig = create_latency_chart(metrics.get("queries_over_time", []))
        st.plotly_chart(latency_fig, use_container_width=True)

    with col2:
        model_fig = create_model_usage_chart(metrics.get("model_usage", {}))
        st.plotly_chart(model_fig, use_container_width=True)

    # Graph stats chart
    graph_stats = metrics.get("graph_stats", {})
    if graph_stats:
        col1, col2 = st.columns(2)
        with col1:
            stats_fig = create_graph_stats_chart(graph_stats)
            st.plotly_chart(stats_fig, use_container_width=True)

        with col2:
            st.markdown("#### 📋 Graph Summary")
            st.markdown(f"""
            | Metric | Value |
            |--------|-------|
            | **Total Nodes** | {graph_stats.get('total_nodes', 0)} |
            | **Total Relationships** | {graph_stats.get('total_relationships', 0)} |
            | **Node Labels** | {', '.join(graph_stats.get('node_labels', []))} |
            | **Relationship Types** | {', '.join(graph_stats.get('relationship_types', []))} |
            """)

    # ── Recent Queries ────────────────────────────────────
    top_queries = metrics.get("top_queries", [])
    if top_queries:
        st.markdown("#### 🕐 Recent Queries")
        for q in top_queries[:5]:
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.text(q.get("query", ""))
            with col2:
                st.text(f"{q.get('latency_ms', 0):.0f}ms")
            with col3:
                st.text(q.get("model", ""))
