"""
Centralized configuration loaded from .env file.
Uses Pydantic Settings for validated, typed configuration.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Neo4j ──────────────────────────────────────────────
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password"
    neo4j_database: str = "neo4j"

    # ── Groq LLM ──────────────────────────────────────────
    groq_api_key: str = ""

    # ── Pinecone Vector DB ─────────────────────────────────
    pinecone_api_key: str = ""
    pinecone_index: str = "rag-index"

    # ── HuggingFace ────────────────────────────────────────
    hf_token: str = ""
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # ── API Security ───────────────────────────────────────
    api_secret_key: str = "default-secret-key"
    rate_limit: str = "30/minute"

    # ── WhatsApp Group Notification ────────────────────────
    whatsapp_group_link: str = "https://chat.whatsapp.com/DIvuKQEblyWKVWm1uf7tlb"

    # ── FAISS ──────────────────────────────────────────────
    faiss_index_dir: str = "faiss_index"

    # ── LLM Models for Comparison ──────────────────────────
    llm_models: list[str] = [
        "openai/gpt-oss-120b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ]
    default_model: str = "llama-3.3-70b-versatile"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
