"""
Multi-LLM Comparison Panel — Side-by-side model comparison with charts.
Fixed: non-overlapping card layout, one model per row, beautiful styling.
"""

import streamlit as st
import plotly.graph_objects as go
from frontend.utils import api_post, api_get


def create_comparison_charts(results: list) -> tuple:
    """Create latency and token usage comparison bar charts."""
    models = [r.get("model", "Unknown").split("/")[-1] for r in results]
    latencies = [r.get("latency_ms", 0) for r in results]
    colors = ["#6366f1", "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b"]

    # Latency chart
    lat_fig = go.Figure(data=[go.Bar(
        x=models, y=latencies,
        marker=dict(
            color=colors[:len(models)],
            line=dict(width=0),
            cornerradius=6,
        ),
        text=[f"{l:.0f}ms" for l in latencies],
        textposition="outside",
        textfont=dict(color="#e2e8f0", size=12, family="Inter"),
    )])
    lat_fig.update_layout(
        title=dict(text="⏱️ Response Latency", font=dict(color="#f1f5f9", size=14)),
        xaxis=dict(color="#64748b", tickfont=dict(size=10)),
        yaxis=dict(title="ms", color="#64748b", showgrid=True, gridcolor="rgba(99,102,241,0.1)"),
        paper_bgcolor="rgba(10,14,26,0)", plot_bgcolor="rgba(17,24,39,0.5)",
        height=280, margin=dict(l=50, r=20, t=50, b=50),
    )

    # Token usage chart
    token_counts = []
    for r in results:
        usage = r.get("token_usage", {})
        token_counts.append(usage.get("total_tokens", usage.get("completion_tokens", 0)))

    tok_fig = go.Figure(data=[go.Bar(
        x=models, y=token_counts,
        marker=dict(color=colors[:len(models)], line=dict(width=0), cornerradius=6),
        text=[str(t) for t in token_counts],
        textposition="outside",
        textfont=dict(color="#e2e8f0", size=12, family="Inter"),
    )])
    tok_fig.update_layout(
        title=dict(text="📊 Token Usage", font=dict(color="#f1f5f9", size=14)),
        xaxis=dict(color="#64748b", tickfont=dict(size=10)),
        yaxis=dict(title="Tokens", color="#64748b", showgrid=True, gridcolor="rgba(99,102,241,0.1)"),
        paper_bgcolor="rgba(10,14,26,0)", plot_bgcolor="rgba(17,24,39,0.5)",
        height=280, margin=dict(l=50, r=20, t=50, b=50),
    )

    return lat_fig, tok_fig


def render_comparison_panel():
    """Render the multi-LLM comparison panel."""

    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <span style="font-size: 1.3rem; font-weight: 700; color: #c4b5fd;">⚖️ Multi-LLM Comparison Engine</span>
        <div style="color: #64748b; font-size: 0.85rem; margin-top: 4px;">
            Run the same query across multiple AI models — compare quality, speed, and cost
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Query input
    comp_query = st.text_input(
        "Enter query to compare across models:",
        placeholder="e.g., What are the top products by revenue?",
        key="comparison_query",
    )

    # Model selection
    models_data = api_get("/api/models")
    available_models = models_data.get("models", [])

    selected_models = st.multiselect(
        "Select models to compare:",
        available_models,
        default=available_models[:3] if len(available_models) >= 3 else available_models,
        key="comparison_models",
    )

    if st.button("🚀 Compare Models", use_container_width=True, key="run_comparison"):
        if not comp_query:
            st.warning("Please enter a query to compare.")
            return

        if len(selected_models) < 2:
            st.warning("Select at least 2 models to compare.")
            return

        with st.spinner("⏳ Running comparison across models... This may take a moment."):
            result = api_post("/api/compare", {
                "query": comp_query,
                "models": selected_models,
            }, timeout=300.0)

            if "error" in result:
                st.error(f"Comparison error: {result['error']}")
                return

            st.session_state["comparison_result"] = result

    # ── Display results ───────────────────────────────────
    if "comparison_result" not in st.session_state:
        return

    result = st.session_state["comparison_result"]
    results = result.get("results", [])
    if not results:
        return

    st.markdown("---")

    # ── Charts side by side ───────────────────────────────
    lat_fig, tok_fig = create_comparison_charts(results)
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(lat_fig, use_container_width=True)
    with col2:
        st.plotly_chart(tok_fig, use_container_width=True)

    st.markdown("---")

    # ── Model responses — ONE PER ROW (no overlap) ────────
    st.markdown("""
    <div style="font-size: 1.1rem; font-weight: 700; color: #e2e8f0; margin-bottom: 12px;">
        📝 Model Responses
    </div>
    """, unsafe_allow_html=True)

    model_colors = ["#6366f1", "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b"]

    for i, r in enumerate(results):
        model_name = r.get("model", "Unknown").split("/")[-1]
        color = model_colors[i % len(model_colors)]
        latency = r.get("latency_ms", 0)
        usage = r.get("token_usage", {})
        tokens = usage.get("total_tokens", usage.get("completion_tokens", "—"))

        if r.get("error"):
            st.markdown(f"""
            <div style="
                background: rgba(244,63,94,0.1);
                border: 1px solid rgba(244,63,94,0.3);
                border-left: 4px solid #f43f5e;
                border-radius: 12px;
                padding: 18px;
                margin-bottom: 16px;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 700; color: #f43f5e;">🤖 {model_name}</span>
                    <span style="color: #f43f5e; font-size: 0.8rem;">ERROR</span>
                </div>
                <div style="color: #fca5a5; margin-top: 8px; font-size: 0.85rem;">{r['error']}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            answer = r.get("answer", "No response")
            st.markdown(f"""
            <div style="
                background: rgba(17,24,39,0.8);
                border: 1px solid rgba(99,102,241,0.2);
                border-left: 4px solid {color};
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 16px;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="font-weight: 700; font-size: 1rem; color: {color};">🤖 {model_name}</span>
                    <div style="display: flex; gap: 12px;">
                        <span style="
                            background: rgba(99,102,241,0.15);
                            color: #a5b4fc;
                            padding: 3px 10px;
                            border-radius: 8px;
                            font-size: 0.75rem;
                        ">⏱️ {latency:.0f}ms</span>
                        <span style="
                            background: rgba(6,182,212,0.15);
                            color: #67e8f9;
                            padding: 3px 10px;
                            border-radius: 8px;
                            font-size: 0.75rem;
                        ">📊 {tokens} tokens</span>
                    </div>
                </div>
                <div style="
                    color: #e2e8f0;
                    font-size: 0.9rem;
                    line-height: 1.7;
                    white-space: pre-wrap;
                ">{answer}</div>
            </div>
            """, unsafe_allow_html=True)
