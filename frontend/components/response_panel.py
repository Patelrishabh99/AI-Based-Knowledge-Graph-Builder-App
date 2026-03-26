"""
Response Panel — Beautiful AI response display with retrieval-path graph.
Shows: AI answer, generated Cypher, raw results, and an animated
graph showing how information was retrieved from the knowledge graph.
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from frontend.utils import format_cypher


def create_retrieval_path_graph(response: dict) -> go.Figure:
    """
    Create a beautiful retrieval-path graph that shows how the query
    flows through the knowledge graph to retrieve information.
    Nodes: Query → Intent → Cypher → Graph Nodes → Response
    """
    cypher = response.get("cypher_query", "")
    raw_results = response.get("raw_results", [])
    intent = response.get("intent", "lookup")
    entities = response.get("entities", [])

    # ── Build the retrieval path nodes ────────────────────
    nodes = []
    edges = []

    # 1. User query node
    nodes.append({
        "id": "query", "label": "🔍 User Query",
        "detail": response.get("query", "")[:40],
        "color": "#6366f1", "size": 18,
        "x": 0, "y": 3,
    })

    # 2. Intent detection
    intent_icons = {"aggregate": "📊", "lookup": "🔎", "comparison": "⚖️", "trend": "📈", "relationship": "🔗"}
    nodes.append({
        "id": "intent", "label": f"{intent_icons.get(intent, '🧠')} Intent: {intent.title()}",
        "detail": f"Detected: {intent}",
        "color": "#8b5cf6", "size": 14,
        "x": -2, "y": 2,
    })
    edges.append(("query", "intent"))

    # 3. Entity nodes
    if entities:
        for i, entity in enumerate(entities[:3]):
            eid = f"entity_{i}"
            entity_colors = {"Customer": "#06b6d4", "Product": "#10b981", "Order": "#f59e0b"}
            nodes.append({
                "id": eid, "label": f"📦 {entity}",
                "detail": f"Graph Entity",
                "color": entity_colors.get(entity, "#94a3b8"), "size": 12,
                "x": -3 + i * 1.5, "y": 1,
            })
            edges.append(("intent", eid))
    else:
        nodes.append({
            "id": "entity_auto", "label": "🔄 Auto-detect",
            "detail": "Schema mapping",
            "color": "#06b6d4", "size": 12,
            "x": -2, "y": 1,
        })
        edges.append(("intent", "entity_auto"))

    # 4. Cypher generation node
    if cypher:
        nodes.append({
            "id": "cypher", "label": "⚡ Cypher Engine",
            "detail": cypher[:35] + "..." if len(cypher) > 35 else cypher,
            "color": "#f59e0b", "size": 16,
            "x": 0, "y": 0,
        })
        for n in nodes:
            if n["id"].startswith("entity"):
                edges.append((n["id"], "cypher"))

    # 5. Knowledge Graph traversal nodes (from raw results)
    if raw_results and isinstance(raw_results, list):
        for i, result in enumerate(raw_results[:5]):
            rid = f"result_{i}"
            if isinstance(result, dict):
                label_text = list(result.values())[0] if result else f"Result {i+1}"
                label_text = str(label_text)[:20]
            else:
                label_text = str(result)[:20]

            angle = (i - 2) * 0.8
            nodes.append({
                "id": rid, "label": f"📄 {label_text}",
                "detail": str(result)[:50] if isinstance(result, dict) else str(result)[:50],
                "color": "#10b981", "size": 10,
                "x": angle * 1.5, "y": -1.5,
            })
            if cypher:
                edges.append(("cypher", rid))

    # 6. RAG node (if sources)
    sources = response.get("sources", [])
    if sources:
        nodes.append({
            "id": "rag", "label": "🧠 RAG Pipeline",
            "detail": f"{len(sources)} sources found",
            "color": "#ec4899", "size": 14,
            "x": 3, "y": 0,
        })
        edges.append(("query", "rag"))

    # 7. Final response node
    nodes.append({
        "id": "response", "label": "✨ AI Response",
        "detail": response.get("answer", "")[:40],
        "color": "#10b981", "size": 18,
        "x": 0, "y": -3,
    })
    # Connect all result nodes and RAG to response
    for n in nodes:
        if n["id"].startswith("result_"):
            edges.append((n["id"], "response"))
    if sources:
        edges.append(("rag", "response"))
    if not raw_results and not sources:
        if cypher:
            edges.append(("cypher", "response"))
        else:
            edges.append(("query", "response"))

    # ── Build the Plotly figure ───────────────────────────
    fig = go.Figure()

    # Draw edges as curved lines
    for src_id, tgt_id in edges:
        src = next((n for n in nodes if n["id"] == src_id), None)
        tgt = next((n for n in nodes if n["id"] == tgt_id), None)
        if src and tgt:
            # Create curved path
            mid_x = (src["x"] + tgt["x"]) / 2 + np.random.uniform(-0.2, 0.2)
            mid_y = (src["y"] + tgt["y"]) / 2

            fig.add_trace(go.Scatter(
                x=[src["x"], mid_x, tgt["x"]],
                y=[src["y"], mid_y, tgt["y"]],
                mode="lines",
                line=dict(color="rgba(139, 92, 246, 0.4)", width=2, shape="spline"),
                hoverinfo="none",
                showlegend=False,
            ))

            # Add arrow annotation
            fig.add_annotation(
                ax=mid_x, ay=mid_y,
                x=tgt["x"], y=tgt["y"],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True,
                arrowhead=2, arrowsize=1, arrowwidth=1.5,
                arrowcolor="rgba(139, 92, 246, 0.5)",
            )

    # Draw nodes
    for n in nodes:
        fig.add_trace(go.Scatter(
            x=[n["x"]], y=[n["y"]],
            mode="markers+text",
            marker=dict(
                size=n["size"] * 2.5,
                color=n["color"],
                opacity=0.9,
                line=dict(width=2, color="rgba(255,255,255,0.3)"),
            ),
            text=[n["label"]],
            textposition="bottom center",
            textfont=dict(size=11, color="#e2e8f0", family="Inter"),
            hovertext=[f"<b>{n['label']}</b><br>{n['detail']}"],
            hoverinfo="text",
            showlegend=False,
        ))

    fig.update_layout(
        title=dict(
            text="🔄 Information Retrieval Path",
            font=dict(color="#f1f5f9", size=14, family="Inter"),
            x=0.5,
        ),
        xaxis=dict(visible=False, range=[-5, 5]),
        yaxis=dict(visible=False, range=[-4.5, 4.5]),
        paper_bgcolor="rgba(10, 14, 26, 0)",
        plot_bgcolor="rgba(10, 14, 26, 0)",
        height=450,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return fig


def render_response_panel(response: dict):
    """Render the response panel with AI answer, retrieval graph, and metadata."""
    if not response:
        return

    # ── AI Answer ─────────────────────────────────────────
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.1));
        border: 1px solid rgba(99,102,241,0.3);
        border-radius: 16px;
        padding: 28px;
        margin: 16px 0;
        animation: fadeInUp 0.6s ease-out;
    ">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 14px;">
            <span style="font-size: 1.4rem;">🤖</span>
            <span style="font-size: 1.1rem; font-weight: 700; color: #c4b5fd;">AI Response</span>
            <span style="
                background: rgba(16,185,129,0.15);
                color: #10b981;
                padding: 3px 10px;
                border-radius: 12px;
                font-size: 0.7rem;
                font-weight: 600;
                border: 1px solid rgba(16,185,129,0.3);
            ">GENERATED</span>
        </div>
        <div style="
            color: #e2e8f0;
            font-size: 1rem;
            line-height: 1.8;
            letter-spacing: 0.01em;
        ">""" + response.get("answer", "No response generated.") + """</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Metadata chips ────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        latency = response.get("latency_ms", 0)
        color = "#10b981" if latency < 3000 else "#f59e0b" if latency < 8000 else "#f43f5e"
        st.markdown(f"""
        <div style="background: rgba(17,24,39,0.8); border: 1px solid rgba(99,102,241,0.2);
                    border-radius: 12px; padding: 14px; text-align: center;">
            <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 1px;">⏱️ Latency</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: {color};">{latency:.0f}ms</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        model = response.get("model_used", "N/A").split("/")[-1]
        st.markdown(f"""
        <div style="background: rgba(17,24,39,0.8); border: 1px solid rgba(99,102,241,0.2);
                    border-radius: 12px; padding: 14px; text-align: center;">
            <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 1px;">🤖 Model</div>
            <div style="font-size: 1rem; font-weight: 600; color: #c4b5fd;">{model}</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        tokens = response.get("token_usage", {})
        total = tokens.get("total_tokens", tokens.get("completion_tokens", "—"))
        st.markdown(f"""
        <div style="background: rgba(17,24,39,0.8); border: 1px solid rgba(99,102,241,0.2);
                    border-radius: 12px; padding: 14px; text-align: center;">
            <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 1px;">📊 Tokens</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: #06b6d4;">{total}</div>
        </div>""", unsafe_allow_html=True)

    with col4:
        intent = response.get("intent", "—").title()
        st.markdown(f"""
        <div style="background: rgba(17,24,39,0.8); border: 1px solid rgba(99,102,241,0.2);
                    border-radius: 12px; padding: 14px; text-align: center;">
            <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 1px;">🎯 Intent</div>
            <div style="font-size: 1rem; font-weight: 600; color: #f59e0b;">{intent}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Retrieval Path Graph ──────────────────────────────
    st.markdown("""
    <div style="
        background: rgba(17,24,39,0.6);
        border: 1px solid rgba(99,102,241,0.2);
        border-radius: 16px;
        padding: 8px;
        margin: 8px 0;
    ">
    """, unsafe_allow_html=True)

    fig = create_retrieval_path_graph(response)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Generated Cypher ──────────────────────────────────
    cypher_text = response.get("cypher_query", "")
    if cypher_text:
        with st.expander("⚡ Generated Cypher Query", expanded=True):
            st.code(format_cypher(cypher_text), language="cypher")

    # ── Raw Results ───────────────────────────────────────
    raw = response.get("raw_results", [])
    if raw:
        with st.expander(f"📋 Graph Results ({len(raw)} records)", expanded=False):
            st.json(raw[:10])

    # ── RAG Sources ───────────────────────────────────────
    sources = response.get("sources", [])
    if sources:
        with st.expander(f"🧠 RAG Sources ({len(sources)} retrieved)", expanded=False):
            for i, source in enumerate(sources, 1):
                st.markdown(f"""
                <div style="
                    background: rgba(17,24,39,0.6);
                    border-left: 3px solid #8b5cf6;
                    padding: 10px 14px;
                    margin: 6px 0;
                    border-radius: 0 8px 8px 0;
                    font-size: 0.85rem;
                    color: #cbd5e1;
                ">{i}. {source}</div>""", unsafe_allow_html=True)
