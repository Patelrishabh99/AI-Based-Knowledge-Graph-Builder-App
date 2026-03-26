"""
Query Input Panel — Natural language query input with suggestions and history.
"""

import streamlit as st


def _set_suggestion(text: str):
    """Callback to set a suggestion into the query input."""
    st.session_state["suggestion_text"] = text


def render_query_panel():
    """Render the query input panel."""

    st.markdown('<div class="animate-fade-in">', unsafe_allow_html=True)

    # Use suggestion if one was clicked
    default_value = st.session_state.pop("suggestion_text", "")

    # Query input
    query = st.text_area(
        "🔍 Ask your Knowledge Graph",
        value=default_value,
        placeholder="e.g., What are the top 5 products by sales? Which customers are in the Consumer segment?",
        height=100,
        key="query_input",
    )

    # Quick suggestions
    st.markdown("**Quick queries:**")
    cols = st.columns(4)
    suggestions = [
        "Top 5 products by sales",
        "Customer segments breakdown",
        "Orders in 2023",
        "Products by category",
    ]

    for i, suggestion in enumerate(suggestions):
        with cols[i]:
            st.button(
                f"💡 {suggestion}",
                key=f"suggest_{i}",
                use_container_width=True,
                on_click=_set_suggestion,
                args=(suggestion,),
            )

    # Controls row
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        use_rag = st.checkbox("🔗 Enable RAG (Semantic + Keyword Search)", value=True, key="use_rag")

    with col2:
        from frontend.utils import api_get
        models_data = api_get("/api/models")
        available_models = models_data.get("models", ["openai/gpt-oss-120b"])
        default_model = models_data.get("default", "openai/gpt-oss-120b")
        selected_model = st.selectbox(
            "🤖 Model",
            available_models,
            index=available_models.index(default_model) if default_model in available_models else 0,
            key="selected_model",
        )

    with col3:
        submit = st.button("🚀 **Ask**", use_container_width=True, key="submit_query")

    st.markdown('</div>', unsafe_allow_html=True)

    return query, submit, use_rag, selected_model
