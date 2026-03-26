"""
Sidebar — Session history, system status, and app info.
"""

import streamlit as st
from frontend.utils import api_get, api_post
from frontend.styles import render_status_badge


def render_sidebar():
    """Render the sidebar with session management and system status."""

    with st.sidebar:
        # ── Logo / Title ──────────────────────────────────
        st.markdown("""
        <div style="text-align: center; padding: 16px 0;">
            <div style="font-size: 2.5rem;">🧠</div>
            <div style="font-size: 1.1rem; font-weight: 700;
                        background: linear-gradient(135deg, #6366f1, #06b6d4);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;">
                Graph Builder
            </div>
            <div style="font-size: 0.75rem; color: #64748b; margin-top: 4px;">
                Enterprise Intelligence v1.0
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # ── System Status ─────────────────────────────────
        st.markdown("#### 🔌 System Status")

        health = api_get("/api/health")
        if "error" not in health:
            neo4j_ok = health.get("neo4j_connected", False)
            pinecone_ok = health.get("pinecone_connected", False)

            st.markdown(
                f"Neo4j: {render_status_badge('Connected', 'success') if neo4j_ok else render_status_badge('Disconnected', 'error')}",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"Pinecone: {render_status_badge('Connected', 'success') if pinecone_ok else render_status_badge('Disconnected', 'warning')}",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"API: {render_status_badge('Online', 'success')}",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"API: {render_status_badge('Offline', 'error')}",
                unsafe_allow_html=True,
            )
            st.caption("Start backend: `uvicorn backend.main:app --reload`")

        st.markdown("---")

        # ── Session Management ────────────────────────────
        st.markdown("#### 💬 Session")

        if "session_id" not in st.session_state:
            if st.button("🆕 New Session", use_container_width=True):
                result = api_post("/api/sessions", {})
                if "session_id" in result:
                    st.session_state["session_id"] = result["session_id"]
                    st.rerun()
        else:
            st.success(f"Session: `{st.session_state['session_id']}`")

            # Show query history
            session_data = api_get(f"/api/sessions/{st.session_state['session_id']}")
            queries = session_data.get("queries", [])

            if queries:
                st.markdown("**Recent Queries:**")
                for q in reversed(queries[-5:]):
                    query_text = q.get("query", "")[:50]
                    st.caption(f"🔹 {query_text}")

            if st.button("🗑️ Clear Session", use_container_width=True):
                st.session_state.pop("session_id", None)
                st.session_state.pop("last_response", None)
                st.rerun()

        st.markdown("---")

        # ── Quick Actions ─────────────────────────────────
        st.markdown("#### ⚡ Quick Actions")

        if st.button("📥 Index Data to Pinecone", use_container_width=True):
            with st.spinner("Indexing..."):
                result = api_post("/api/index", {})
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success("Indexing complete!")

        if st.button("📋 View Graph Schema", use_container_width=True):
            schema = api_get("/api/schema")
            if "error" not in schema:
                st.code(schema.get("schema", ""), language="text")
            else:
                st.error("Cannot fetch schema")

        st.markdown("---")

        # ── Footer ────────────────────────────────────────
        st.markdown("""
        <div style="text-align: center; padding: 8px 0;">
            <div style="font-size: 0.7rem; color: #475569;">
                Built with ❤️ using<br>
                Streamlit • FastAPI • Neo4j • LangChain
            </div>
        </div>
        """, unsafe_allow_html=True)
