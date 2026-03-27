"""
Notification Service — Generates shareable WhatsApp deep links
for sending query activity summaries to the project group.
"""

import logging
from urllib.parse import quote
from datetime import datetime
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def format_query_notification(
    query: str,
    model: str,
    answer_summary: str,
    response_type: str = "text",
    latency_ms: float = 0,
    intent: str = "",
) -> dict:
    """
    Format a query activity into a shareable notification.
    Returns the formatted message and WhatsApp deep link.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")

    # Build the message
    message_lines = [
        "🧠 *AI Graph Builder — Query Activity*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"📝 *Query:* {query}",
        f"🤖 *Model:* {model}",
        f"🎯 *Intent:* {intent or 'auto-detected'}",
        f"📄 *Response Type:* {response_type}",
        f"⏱️ *Latency:* {latency_ms:.0f}ms",
        "",
        f"💬 *Answer Preview:*",
        f"{_truncate(answer_summary, 300)}",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"🕐 {timestamp}",
        "🔗 _Sent from AI Graph Builder Enterprise_",
    ]

    message = "\n".join(message_lines)

    # Generate WhatsApp deep link
    whatsapp_url = _generate_whatsapp_link(message)

    return {
        "message": message,
        "whatsapp_url": whatsapp_url,
        "timestamp": timestamp,
    }


def _generate_whatsapp_link(message: str) -> str:
    """
    Generate a WhatsApp deep link with pre-filled message.
    Uses the group invite link from settings or the wa.me API.
    """
    encoded_message = quote(message)

    # Use the WhatsApp API for sharing with pre-filled text
    # This opens WhatsApp with the message ready to send
    whatsapp_url = f"https://api.whatsapp.com/send?text={encoded_message}"

    return whatsapp_url


def get_group_link() -> str:
    """Get the configured WhatsApp group link."""
    return settings.whatsapp_group_link


def _truncate(text: str, max_len: int = 300) -> str:
    """Truncate text with ellipsis."""
    if not text:
        return "—"
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."
