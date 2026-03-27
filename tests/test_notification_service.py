"""
Tests for the notification service.
"""

import pytest
from unittest.mock import patch


class TestNotificationService:
    """Test notification service functionality."""

    def test_format_query_notification(self):
        """Should format a notification message correctly."""
        from backend.services.notification_service import format_query_notification
        result = format_query_notification(
            query="Top 5 products by sales",
            model="llama-3.3-70b-versatile",
            answer_summary="The top products are Widget A, Widget B...",
            response_type="text",
            latency_ms=450.0,
            intent="aggregate",
        )

        assert "message" in result
        assert "whatsapp_url" in result
        assert "timestamp" in result
        assert "Top 5 products by sales" in result["message"]
        assert "llama-3.3-70b-versatile" in result["message"]
        assert result["whatsapp_url"].startswith("https://api.whatsapp.com/send?text=")

    def test_whatsapp_url_encoding(self):
        """WhatsApp URL should properly encode special characters."""
        from backend.services.notification_service import format_query_notification
        result = format_query_notification(
            query="What is 1+1?",
            model="test-model",
            answer_summary="The answer is 2.",
        )
        url = result["whatsapp_url"]
        assert "https://api.whatsapp.com/send?text=" in url
        # Check that special chars are encoded
        assert "?" not in url.split("text=", 1)[1] or "%3F" in url

    def test_get_group_link(self):
        """Should return the configured group link."""
        from backend.services.notification_service import get_group_link
        link = get_group_link()
        assert "whatsapp.com" in link

    def test_truncate_long_answer(self):
        """Should truncate long answers."""
        from backend.services.notification_service import _truncate
        long_text = "A" * 500
        assert len(_truncate(long_text, 300)) == 303  # 300 + "..."

    def test_truncate_short_answer(self):
        """Should not truncate short text."""
        from backend.services.notification_service import _truncate
        short_text = "Hello world"
        assert _truncate(short_text, 300) == short_text

    def test_truncate_empty(self):
        """Should handle empty string."""
        from backend.services.notification_service import _truncate
        assert _truncate("", 300) == "—"

    def test_message_format_includes_all_fields(self):
        """Message should include all query details."""
        from backend.services.notification_service import format_query_notification
        result = format_query_notification(
            query="Customer segments breakdown",
            model="openai/gpt-oss-120b",
            answer_summary="Consumer, Corporate, and Home Office segments.",
            response_type="text",
            latency_ms=1250.5,
            intent="aggregate",
        )
        msg = result["message"]
        assert "Customer segments breakdown" in msg
        assert "openai/gpt-oss-120b" in msg
        assert "aggregate" in msg
        assert "1251ms" in msg or "1250ms" in msg  # rounded
        assert "AI Graph Builder" in msg
