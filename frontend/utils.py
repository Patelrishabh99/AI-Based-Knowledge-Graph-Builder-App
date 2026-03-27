"""
Utility helpers for the Streamlit frontend.
"""

import httpx
import os

# Support both env vars and Streamlit secrets (for Streamlit Cloud deployment)
try:
    import streamlit as st
    _secrets = dict(st.secrets) if hasattr(st, "secrets") else {}
except Exception:
    _secrets = {}

BACKEND_URL = os.getenv("BACKEND_URL", _secrets.get("BACKEND_URL", "http://localhost:8000"))
API_KEY = os.getenv("API_SECRET_KEY", _secrets.get("API_SECRET_KEY", ""))


def _headers() -> dict:
    """Build request headers including API key."""
    h = {"Content-Type": "application/json"}
    if API_KEY:
        h["X-API-Key"] = API_KEY
    return h


def api_post(endpoint: str, data: dict, timeout: float = 120.0) -> dict:
    """Make a POST request to the backend API."""
    try:
        response = httpx.post(
            f"{BACKEND_URL}{endpoint}",
            json=data,
            headers=_headers(),
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()
    except httpx.TimeoutException:
        return {"error": "Request timed out. The query may be too complex."}
    except httpx.HTTPStatusError as e:
        return {"error": f"API error: {e.response.status_code} - {e.response.text}"}
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}


def api_get(endpoint: str, timeout: float = 30.0) -> dict:
    """Make a GET request to the backend API."""
    try:
        response = httpx.get(
            f"{BACKEND_URL}{endpoint}",
            headers=_headers(),
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}


def format_cypher(cypher: str) -> str:
    """Basic Cypher formatting for display."""
    if not cypher:
        return ""
    keywords = ["MATCH", "WHERE", "RETURN", "WITH", "ORDER BY", "LIMIT",
                 "MERGE", "CREATE", "SET", "OPTIONAL MATCH", "UNWIND"]
    formatted = cypher
    for kw in keywords:
        formatted = formatted.replace(f" {kw} ", f"\n{kw} ")
    return formatted.strip()


def truncate(text: str, max_len: int = 200) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."
