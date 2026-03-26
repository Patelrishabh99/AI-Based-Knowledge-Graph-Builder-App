"""
3D Graph Visualization Panel — Interactive Plotly 3D scatter + edges.
Color-coded nodes by type with hover tooltips, zoom, rotate, filter.
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from frontend.utils import api_post


# Color mapping for node types
NODE_COLORS = {
    "Customer": {"color": "#6366f1", "symbol": "circle"},
    "Product": {"color": "#10b981", "symbol": "diamond"},
    "Order": {"color": "#f59e0b", "symbol": "square"},
    "Node": {"color": "#94a3b8", "symbol": "circle"},
}


def create_3d_graph(graph_data: dict) -> go.Figure:
    """Create an interactive 3D graph visualization using Plotly."""
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    if not nodes:
        fig = go.Figure()
        fig.update_layout(
            title="No graph data available",
            paper_bgcolor="#0a0e1a",
            plot_bgcolor="#0a0e1a",
        )
        return fig

    # Assign 3D positions using spring-like layout
    n = len(nodes)
    np.random.seed(42)

    # Simple force-directed positions
    positions = {}
    for i, node in enumerate(nodes):
        angle = 2 * np.pi * i / n
        radius = 3 + np.random.uniform(-1, 1)
        z_offset = np.random.uniform(-2, 2)

        # Group by type
        node_type = node.get("type", "Node")
        if node_type == "Customer":
            z_offset += 3
        elif node_type == "Product":
            z_offset -= 3

        positions[node["id"]] = (
            radius * np.cos(angle) + np.random.uniform(-0.5, 0.5),
            radius * np.sin(angle) + np.random.uniform(-0.5, 0.5),
            z_offset,
        )

    fig = go.Figure()

    # ── Draw edges ────────────────────────────────────────
    edge_x, edge_y, edge_z = [], [], []
    for edge in edges:
        src = positions.get(edge["source"])
        tgt = positions.get(edge["target"])
        if src and tgt:
            edge_x.extend([src[0], tgt[0], None])
            edge_y.extend([src[1], tgt[1], None])
            edge_z.extend([src[2], tgt[2], None])

    fig.add_trace(go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        mode="lines",
        line=dict(color="rgba(99, 102, 241, 0.3)", width=1.5),
        hoverinfo="none",
        name="Relationships",
    ))

    # ── Draw nodes by type ────────────────────────────────
    node_types = set(n.get("type", "Node") for n in nodes)

    for ntype in node_types:
        type_nodes = [n for n in nodes if n.get("type", "Node") == ntype]
        color_info = NODE_COLORS.get(ntype, NODE_COLORS["Node"])

        x_vals = [positions[n["id"]][0] for n in type_nodes if n["id"] in positions]
        y_vals = [positions[n["id"]][1] for n in type_nodes if n["id"] in positions]
        z_vals = [positions[n["id"]][2] for n in type_nodes if n["id"] in positions]

        # Build hover text
        hover_texts = []
        for n in type_nodes:
            if n["id"] in positions:
                props = n.get("properties", {})
                text = f"<b>{n['label']}</b><br>Type: {ntype}"
                for k, v in list(props.items())[:5]:
                    text += f"<br>{k}: {v}"
                hover_texts.append(text)

        fig.add_trace(go.Scatter3d(
            x=x_vals, y=y_vals, z=z_vals,
            mode="markers+text",
            marker=dict(
                size=8 if ntype != "Order" else 5,
                color=color_info["color"],
                symbol=color_info["symbol"],
                opacity=0.9,
                line=dict(width=1, color="rgba(255,255,255,0.3)"),
            ),
            text=[n["label"][:15] for n in type_nodes if n["id"] in positions],
            textposition="top center",
            textfont=dict(size=8, color="#94a3b8"),
            hovertext=hover_texts,
            hoverinfo="text",
            name=f"{ntype} ({len(type_nodes)})",
        ))

    # ── Layout ────────────────────────────────────────────
    fig.update_layout(
        title=dict(
            text=f"Knowledge Graph — {len(nodes)} Nodes, {len(edges)} Relationships",
            font=dict(color="#f1f5f9", size=14),
        ),
        showlegend=True,
        legend=dict(
            font=dict(color="#94a3b8", size=11),
            bgcolor="rgba(17, 24, 39, 0.8)",
            bordercolor="rgba(99, 102, 241, 0.3)",
            borderwidth=1,
        ),
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            bgcolor="#0a0e1a",
        ),
        paper_bgcolor="#0a0e1a",
        plot_bgcolor="#0a0e1a",
        margin=dict(l=0, r=0, t=40, b=0),
        height=600,
    )

    return fig


def render_graph_panel():
    """Render the 3D graph visualization panel."""

    st.markdown("### 🌐 Knowledge Graph Explorer")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        node_type = st.selectbox(
            "Filter by Node Type",
            ["All", "Customer", "Product", "Order"],
            key="graph_node_filter",
        )
    with col2:
        rel_type = st.selectbox(
            "Filter by Relationship",
            ["All", "PLACED", "CONTAINS"],
            key="graph_rel_filter",
        )
    with col3:
        limit = st.slider("Max Nodes", 10, 300, 100, key="graph_limit")

    # Fetch graph data
    if st.button("🔄 Load Graph", use_container_width=True, key="load_graph"):
        with st.spinner("Loading graph data..."):
            data = api_post("/api/graph", {
                "node_type": node_type if node_type != "All" else None,
                "relationship_type": rel_type if rel_type != "All" else None,
                "limit": limit,
            })

            if "error" in data:
                st.error(f"Error: {data['error']}")
            else:
                st.session_state["graph_data"] = data

    # Render graph
    if "graph_data" in st.session_state and st.session_state["graph_data"]:
        data = st.session_state["graph_data"]
        fig = create_3d_graph(data)
        st.plotly_chart(fig, use_container_width=True)

        # Stats
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Nodes", len(nodes))
        with col2:
            st.metric("Relationships", len(edges))
        with col3:
            types = set(n.get("type", "?") for n in nodes)
            st.metric("Node Types", len(types))
    else:
        st.info("👆 Click **Load Graph** to visualize the knowledge graph.")
