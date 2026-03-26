"""
Main Streamlit App — AI-Based Graph Builder for Enterprise Intelligence.
Unified single-page layout: Query + Response + Retrieval Graph on the same page.
"""

import streamlit as st
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="AI Graph Builder — Enterprise Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Apply Custom Theme ────────────────────────────────────────
from frontend.styles import get_custom_css
st.markdown(get_custom_css(), unsafe_allow_html=True)

# ── Import Components ─────────────────────────────────────────
from frontend.components.sidebar import render_sidebar
from frontend.components.query_panel import render_query_panel
from frontend.components.response_panel import render_response_panel
from frontend.components.graph_panel import render_graph_panel
from frontend.components.dashboard_panel import render_dashboard_panel
from frontend.components.comparison_panel import render_comparison_panel
from frontend.utils import api_post

# ── Sidebar ───────────────────────────────────────────────────
render_sidebar()

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div style="text-align: center; padding: 12px 0 4px 0;">
    <div class="main-title">🧠 AI-Based Graph Builder</div>
    <div class="subtitle">Enterprise Intelligence powered by Knowledge Graphs • RAG • Multi-LLM</div>
</div>
""", unsafe_allow_html=True)

# ── Tab Navigation ────────────────────────────────────────────
tab_query, tab_graph, tab_compare, tab_dashboard = st.tabs([
    "💬 Query & Response",
    "🌐 3D Graph Explorer",
    "⚖️ LLM Comparison",
    "📊 Dashboard",
])


# ══════════════════════════════════════════════════════════════
#  TAB 1: QUERY & RESPONSE (everything on one page)
# ══════════════════════════════════════════════════════════════
with tab_query:
    query, submit, use_rag, selected_model = render_query_panel()

    if submit and query:
        with st.spinner("🔄 Querying Knowledge Graph & generating response..."):
            response = api_post("/api/query", {
                "query": query,
                "session_id": st.session_state.get("session_id"),
                "model": selected_model,
                "use_rag": use_rag,
            }, timeout=180.0)

            if "error" in response:
                st.error(f"❌ {response['error']}")
            else:
                st.session_state["last_response"] = response

    # Render the full response (answer + graph + cypher + sources)
    if "last_response" in st.session_state:
        render_response_panel(st.session_state["last_response"])


# ══════════════════════════════════════════════════════════════
#  TAB 2: 3D GRAPH EXPLORER
# ══════════════════════════════════════════════════════════════
with tab_graph:
    render_graph_panel()


# ══════════════════════════════════════════════════════════════
#  TAB 3: MULTI-LLM COMPARISON
# ══════════════════════════════════════════════════════════════
with tab_compare:
    render_comparison_panel()


# ══════════════════════════════════════════════════════════════
#  TAB 4: ENTERPRISE DASHBOARD
# ══════════════════════════════════════════════════════════════
with tab_dashboard:
    render_dashboard_panel()
