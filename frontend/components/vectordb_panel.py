"""
Vector DB Comparison Panel — FAISS vs Pinecone detailed comparison.
Uses Streamlit-native components (st.dataframe, st.columns, st.metric)
instead of raw HTML tables which Streamlit sanitizes/strips.
"""

import streamlit as st
import pandas as pd
from frontend.utils import api_post, api_get


def render_vectordb_panel():
    """Render the FAISS vs Pinecone comparison panel."""

    # ── Section Header ────────────────────────────────────
    st.markdown("## 🔬 Vector Database Comparison")
    st.markdown("**FAISS (Local)** vs **Pinecone (Cloud)** — Side-by-Side Analysis")
    st.divider()

    # ── Property Comparison Table ─────────────────────────
    st.markdown("### 📋 Property Comparison")

    comparison_data = api_get("/api/vectordb/comparison")

    if "error" not in comparison_data:
        props = comparison_data.get("properties", {})
        faiss_props = props.get("faiss", {})
        pinecone_props = props.get("pinecone", {})

        _render_comparison_table(faiss_props, pinecone_props)

        # ── Stats Section ─────────────────────────────────
        st.divider()
        st.markdown("### 📊 Current Index Status")

        col1, col2 = st.columns(2)

        with col1:
            faiss_stats = comparison_data.get("faiss_stats", {})
            _render_stats_card("FAISS", faiss_stats, "⚡")

        with col2:
            pinecone_stats = comparison_data.get("pinecone_stats", {})
            _render_stats_card("Pinecone", pinecone_stats, "🌐")
    else:
        st.warning("⚠️ Could not load comparison data. Make sure the backend is running.")

    # ── Live Benchmark Section ────────────────────────────
    st.divider()
    st.markdown("### ⚡ Live Benchmark")
    st.caption("Run the same query against both FAISS and Pinecone to compare speed and results.")

    col1, col2 = st.columns([3, 1])
    with col1:
        bench_query = st.text_input(
            "🔍 Benchmark Query",
            value="top products in electronics",
            placeholder="Enter a query to benchmark...",
            key="benchmark_query",
        )
    with col2:
        top_k = st.number_input("Top K", min_value=1, max_value=20, value=5, key="bench_top_k")

    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])

    with col_btn1:
        run_benchmark = st.button("🏁 Run Benchmark", use_container_width=True, key="run_benchmark")

    with col_btn2:
        index_faiss = st.button("📥 Index to FAISS", use_container_width=True, key="index_faiss_btn")

    if index_faiss:
        with st.spinner("🔄 Building FAISS index from Neo4j data..."):
            result = api_post("/api/vectordb/index-faiss", {})
            if "error" in result:
                st.error(f"❌ {result['error']}")
            elif result.get("status") == "success":
                st.success(f"✅ FAISS index built! {result.get('count', 0)} vectors, {result.get('index_time_ms', 0):.0f}ms")
            else:
                st.warning(f"⚠️ {result.get('message', 'Unknown status')}")

    if run_benchmark and bench_query:
        with st.spinner("🏁 Running benchmark on both vector databases..."):
            results = api_post("/api/vectordb/benchmark", {
                "query": bench_query,
                "top_k": int(top_k),
            })

            if "error" in results:
                st.error(f"❌ {results['error']}")
            else:
                st.session_state["benchmark_results"] = results

    # Show benchmark results
    if "benchmark_results" in st.session_state:
        _render_benchmark_results(st.session_state["benchmark_results"])

    # ── Recommendation Section ────────────────────────────
    st.divider()
    _render_recommendation()


def _render_comparison_table(faiss_props: dict, pinecone_props: dict):
    """Render the comparison as a styled Streamlit dataframe."""

    properties = [
        ("Full Name", "full_name"),
        ("Hosting", "hosting"),
        ("Cost", "cost"),
        ("Scalability", "scalability"),
        ("Latency", "latency"),
        ("Max Vectors", "max_vectors"),
        ("Persistence", "persistence"),
        ("Metadata Filtering", "filtering"),
        ("Managed Service", "managed_service"),
        ("Real-time Updates", "real_time_updates"),
        ("Multi-tenancy", "multi_tenancy"),
        ("Cloud Native", "cloud_native"),
        ("Index Types", "index_types"),
        ("Best For", "best_for"),
        ("Language", "language"),
        ("Maintained By", "maintained_by"),
    ]

    # Build a pandas DataFrame for native Streamlit rendering
    rows = []
    for label, key in properties:
        rows.append({
            "Property": label,
            "⚡ FAISS (Local)": faiss_props.get(key, "—"),
            "🌐 Pinecone (Cloud)": pinecone_props.get(key, "—"),
        })

    df = pd.DataFrame(rows)
    df = df.set_index("Property")

    st.dataframe(
        df,
        use_container_width=True,
        height=620,
    )


def _render_stats_card(name: str, stats: dict, icon: str):
    """Render a stats card for a vector DB using native Streamlit components."""
    if not stats:
        st.info(f"{icon} **{name}** — Not connected / No data")
        return

    is_connected = stats.get("loaded", stats.get("connected", False))
    vectors = stats.get("total_vectors", stats.get("total_vector_count", 0))
    dimension = stats.get("dimension", "—")

    status = "🟢 ACTIVE" if is_connected else "🔴 INACTIVE"

    st.markdown(f"#### {icon} {name} {status}")
    mc1, mc2 = st.columns(2)
    mc1.metric("Vectors", f"{vectors:,}")
    mc2.metric("Dimension", dimension)


def _render_benchmark_results(results: dict):
    """Render benchmark comparison results using native Streamlit components."""
    faiss_data = results.get("faiss", {})
    pinecone_data = results.get("pinecone", {})

    st.markdown("#### 🏁 Benchmark Results")

    # Latency comparison with st.metric
    col1, col2, col3 = st.columns(3)

    with col1:
        faiss_latency = faiss_data.get("latency_ms", 0)
        faiss_count = faiss_data.get("result_count", 0)
        st.metric("⚡ FAISS", f"{faiss_latency:.1f} ms", f"{faiss_count} results")

    with col2:
        pinecone_latency = pinecone_data.get("latency_ms", 0)
        pinecone_count = pinecone_data.get("result_count", 0)
        st.metric("🌐 Pinecone", f"{pinecone_latency:.1f} ms", f"{pinecone_count} results")

    with col3:
        if faiss_latency > 0 and pinecone_latency > 0:
            ratio = pinecone_latency / faiss_latency
            winner = "FAISS" if ratio > 1 else "Pinecone"
            speedup = f"{ratio:.1f}x" if ratio > 1 else f"{1/ratio:.1f}x"
        else:
            winner = "—"
            speedup = "N/A"
        st.metric("🏆 Speed Winner", winner, f"{speedup} faster")

    # Detailed results
    col_r1, col_r2 = st.columns(2)

    with col_r1:
        with st.expander("⚡ FAISS Results", expanded=False):
            faiss_results = faiss_data.get("results", [])
            if faiss_results:
                for i, r in enumerate(faiss_results, 1):
                    text = r.get("text", "—")[:80]
                    score = r.get("score", 0)
                    st.markdown(f"**{i}.** {text} — *score: {score:.4f}*")
            else:
                st.info("No FAISS results. Click 'Index to FAISS' first.")

    with col_r2:
        with st.expander("🌐 Pinecone Results", expanded=False):
            pine_results = pinecone_data.get("results", [])
            if pine_results:
                for i, r in enumerate(pine_results, 1):
                    text = r.get("text", "—")[:80]
                    score = r.get("score", 0)
                    st.markdown(f"**{i}.** {text} — *score: {score:.4f}*")
            else:
                st.info("No Pinecone results. Index data via sidebar first.")


def _render_recommendation():
    """Render the recommendation section using native Streamlit components."""

    st.markdown("### 🏆 Our Project Uses: Pinecone (Recommended for Production)")

    st.markdown(
        "This enterprise AI Graph Builder uses **Pinecone** as the "
        "production vector database because:"
    )

    st.markdown("""
- ✅ **Zero-ops managed service** — No infrastructure to maintain
- ✅ **Real-time upserts** — Instantly searchable after indexing
- ✅ **Metadata filtering** — Rich filtering by node type, region, category
- ✅ **Horizontal scaling** — Handles millions of vectors effortlessly
- ✅ **High availability** — Cloud-native with built-in redundancy
- ✅ **Multi-tenancy** — Namespace isolation for different data domains
    """)

    st.info(
        "⚡ **When to Choose FAISS Instead**\n\n"
        "FAISS is ideal for **offline/local development**, **privacy-sensitive workloads** "
        "(data stays on your machine), **cost-sensitive projects** (completely free), "
        "and **sub-millisecond latency** requirements where network overhead is unacceptable. "
        "It is also great for **prototyping and benchmarking** before committing to a cloud solution."
    )
