"""
Session Memory service.
Stores query history and context for follow-up conversations.
"""

import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ── In-memory session store ───────────────────────────────────
_sessions: dict[str, dict] = {}


def create_session() -> str:
    """Create a new session and return its ID."""
    session_id = str(uuid.uuid4())[:8]
    _sessions[session_id] = {
        "id": session_id,
        "queries": [],
        "created_at": datetime.utcnow().isoformat(),
        "last_active": datetime.utcnow().isoformat(),
    }
    logger.info("Created session: %s", session_id)
    return session_id


def get_session(session_id: str) -> dict:
    """Get session data by ID. Creates a new session if not found."""
    if session_id not in _sessions:
        _sessions[session_id] = {
            "id": session_id,
            "queries": [],
            "created_at": datetime.utcnow().isoformat(),
            "last_active": datetime.utcnow().isoformat(),
        }
    return _sessions[session_id]


def add_query_to_session(session_id: str, query: str, response: str, cypher: str = "", model: str = ""):
    """Record a query and its response in the session."""
    session = get_session(session_id)
    session["queries"].append({
        "query": query,
        "response": response,
        "cypher": cypher,
        "model": model,
        "timestamp": datetime.utcnow().isoformat(),
    })
    session["last_active"] = datetime.utcnow().isoformat()

    # Keep only last 50 queries per session
    if len(session["queries"]) > 50:
        session["queries"] = session["queries"][-50:]


def get_session_context(session_id: str, last_n: int = 3) -> str:
    """
    Get recent conversation context from the session.
    Used for context-aware follow-up queries.
    """
    session = get_session(session_id)
    recent = session["queries"][-last_n:] if session["queries"] else []

    if not recent:
        return ""

    context_parts = ["=== Recent Conversation Context ==="]
    for q in recent:
        context_parts.append(f"Q: {q['query']}")
        context_parts.append(f"A: {q['response'][:200]}...")  # truncate long responses

    return "\n".join(context_parts)


def get_all_sessions() -> list[dict]:
    """Return all active sessions (summary only)."""
    return [
        {
            "id": s["id"],
            "query_count": len(s["queries"]),
            "created_at": s["created_at"],
            "last_active": s["last_active"],
            "last_query": s["queries"][-1]["query"] if s["queries"] else "",
        }
        for s in _sessions.values()
    ]


def clear_session(session_id: str):
    """Clear a session."""
    if session_id in _sessions:
        del _sessions[session_id]
