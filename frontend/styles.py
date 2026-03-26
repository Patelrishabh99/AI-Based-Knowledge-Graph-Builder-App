"""
Enterprise Dark Theme CSS for the Streamlit UI.
Features: dark mode, glassmorphism, gradient accents, smooth animations.
"""


def get_custom_css() -> str:
    """Return the full custom CSS for the application."""
    return """
    <style>
    /* ══════════════════════════════════════════════════════════
       GLOBAL THEME — Deep Navy Dark Mode
       ══════════════════════════════════════════════════════════ */

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    :root {
        --bg-primary: #0a0e1a;
        --bg-secondary: #111827;
        --bg-card: rgba(17, 24, 39, 0.8);
        --bg-card-hover: rgba(30, 41, 59, 0.9);
        --border: rgba(99, 102, 241, 0.2);
        --border-hover: rgba(99, 102, 241, 0.5);
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --accent-blue: #6366f1;
        --accent-purple: #8b5cf6;
        --accent-cyan: #06b6d4;
        --accent-emerald: #10b981;
        --accent-amber: #f59e0b;
        --accent-rose: #f43f5e;
        --gradient-primary: linear-gradient(135deg, #6366f1, #8b5cf6);
        --gradient-accent: linear-gradient(135deg, #06b6d4, #6366f1);
        --shadow-glow: 0 0 20px rgba(99, 102, 241, 0.15);
    }

    /* Global overrides */
    .stApp {
        background: var(--bg-primary) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: var(--text-primary) !important;
    }

    /* Header */
    header[data-testid="stHeader"] {
        background: rgba(10, 14, 26, 0.95) !important;
        backdrop-filter: blur(12px) !important;
        border-bottom: 1px solid var(--border) !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border) !important;
    }

    section[data-testid="stSidebar"] .stMarkdown {
        color: var(--text-primary) !important;
    }

    /* ── Cards / Containers ──────────────────────────────── */
    .glass-card {
        background: var(--bg-card) !important;
        backdrop-filter: blur(16px) !important;
        border: 1px solid var(--border) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        margin-bottom: 16px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: var(--shadow-glow) !important;
    }

    .glass-card:hover {
        border-color: var(--border-hover) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 32px rgba(99, 102, 241, 0.2) !important;
    }

    /* ── KPI Metric Cards ────────────────────────────────── */
    .kpi-card {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 20px !important;
        text-align: center !important;
    }

    .kpi-value {
        font-size: 2rem !important;
        font-weight: 700 !important;
        background: var(--gradient-primary) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        margin: 8px 0 !important;
    }

    .kpi-label {
        font-size: 0.85rem !important;
        color: var(--text-secondary) !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }

    /* ── Tabs ────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background: transparent !important;
        border-bottom: 1px solid var(--border) !important;
        padding-bottom: 0 !important;
    }

    .stTabs [data-baseweb="tab"] {
        color: var(--text-secondary) !important;
        background: transparent !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 12px 24px !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text-primary) !important;
        background: rgba(99, 102, 241, 0.1) !important;
    }

    .stTabs [aria-selected="true"] {
        color: var(--accent-blue) !important;
        border-bottom: 2px solid var(--accent-blue) !important;
        background: rgba(99, 102, 241, 0.08) !important;
    }

    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 24px !important;
    }

    /* ── Buttons ─────────────────────────────────────────── */
    .stButton > button {
        background: var(--gradient-primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 10px 28px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 25px rgba(99, 102, 241, 0.45) !important;
    }

    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* ── Text Input ──────────────────────────────────────── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
        font-family: 'Inter', sans-serif !important;
        transition: border-color 0.3s !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent-blue) !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
    }

    /* ── Select / Multiselect ────────────────────────────── */
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
    }

    /* ── Code blocks ─────────────────────────────────────── */
    .stCodeBlock {
        background: #0d1117 !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
    }

    /* ── Expander ─────────────────────────────────────────── */
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
    }

    /* ── Dividers ─────────────────────────────────────────── */
    hr {
        border-color: var(--border) !important;
        opacity: 0.5 !important;
    }

    /* ── Metric Elements ──────────────────────────────────── */
    [data-testid="stMetric"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 16px !important;
    }

    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
    }

    [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
    }

    /* ── Scrollbar ────────────────────────────────────────── */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: var(--bg-primary);
    }
    ::-webkit-scrollbar-thumb {
        background: var(--border);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-blue);
    }

    /* ── Title gradient ───────────────────────────────────── */
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1, #8b5cf6, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }

    .subtitle {
        color: var(--text-secondary);
        font-size: 1rem;
        font-weight: 400;
        margin-bottom: 24px;
    }

    /* ── Status badges ────────────────────────────────────── */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .status-success {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .status-warning {
        background: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }

    .status-error {
        background: rgba(244, 63, 94, 0.15);
        color: #f43f5e;
        border: 1px solid rgba(244, 63, 94, 0.3);
    }

    /* ── Response container ───────────────────────────────── */
    .response-box {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 20px;
        margin: 12px 0;
        line-height: 1.7;
        color: var(--text-primary);
    }

    /* ── Animations ────────────────────────────────────────── */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 15px rgba(99, 102, 241, 0.2); }
        50% { box-shadow: 0 0 30px rgba(99, 102, 241, 0.4); }
    }

    .animate-fade-in {
        animation: fadeInUp 0.5s ease-out;
    }

    .pulse-glow {
        animation: pulse-glow 2s ease-in-out infinite;
    }

    /* ── Hide Streamlit defaults ──────────────────────────── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """


def render_kpi_card(label: str, value: str, icon: str = "📊") -> str:
    """Render a KPI metric card as HTML."""
    return f"""
    <div class="kpi-card">
        <div style="font-size: 1.5rem;">{icon}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
    </div>
    """


def render_status_badge(text: str, status: str = "success") -> str:
    """Render a status badge."""
    return f'<span class="status-badge status-{status}">{text}</span>'
