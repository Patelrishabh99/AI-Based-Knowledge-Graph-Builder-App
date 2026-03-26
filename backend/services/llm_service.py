"""
Multi-LLM service powered by Groq.
Supports running queries across multiple models and comparing results.
"""

import time
import logging
from typing import Optional
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── LLM Instance Cache ────────────────────────────────────────
_llm_cache: dict[str, ChatGroq] = {}


def get_llm(model_name: Optional[str] = None) -> ChatGroq:
    """Get or create a ChatGroq LLM instance for the given model."""
    model = model_name or settings.default_model
    if model not in _llm_cache:
        _llm_cache[model] = ChatGroq(
            groq_api_key=settings.groq_api_key,
            model_name=model,
            temperature=0.1,
            max_tokens=2048,
        )
        logger.info("Created LLM instance: %s", model)
    return _llm_cache[model]


def generate_response(
    query: str,
    context: str = "",
    model_name: Optional[str] = None,
    system_prompt: Optional[str] = None,
) -> dict:
    """
    Generate a response from the LLM with optional context injection.

    Returns:
        dict with keys: answer, model, latency_ms, token_usage
    """
    model = model_name or settings.default_model
    llm = get_llm(model)

    # Build messages
    sys_prompt = system_prompt or (
        "You are an intelligent enterprise AI assistant. "
        "Answer questions based on the provided knowledge graph data and context. "
        "Be precise, analytical, and provide actionable insights. "
        "If data is provided, reference specific numbers and entities."
    )

    messages = [SystemMessage(content=sys_prompt)]

    if context:
        messages.append(HumanMessage(content=f"Context data:\n{context}\n\nQuestion: {query}"))
    else:
        messages.append(HumanMessage(content=query))

    # Generate with timing
    start = time.time()
    try:
        response = llm.invoke(messages)
        latency_ms = (time.time() - start) * 1000

        # Extract token usage if available
        token_usage = {}
        if hasattr(response, "response_metadata"):
            meta = response.response_metadata
            if "token_usage" in meta:
                token_usage = meta["token_usage"]
            elif "usage" in meta:
                token_usage = meta["usage"]

        return {
            "answer": response.content,
            "model": model,
            "latency_ms": round(latency_ms, 2),
            "token_usage": token_usage,
        }
    except Exception as e:
        latency_ms = (time.time() - start) * 1000
        logger.error("LLM error (%s): %s", model, e)
        return {
            "answer": f"Error generating response: {str(e)}",
            "model": model,
            "latency_ms": round(latency_ms, 2),
            "token_usage": {},
            "error": str(e),
        }


def compare_models(query: str, context: str = "", models: Optional[list[str]] = None) -> list[dict]:
    """
    Run the same query across multiple LLM models and return comparison results.
    Each result includes: answer, model, latency_ms, token_usage, error (if any).
    """
    model_list = models or settings.llm_models
    results = []

    for model in model_list:
        logger.info("Comparing model: %s", model)
        result = generate_response(query, context=context, model_name=model)
        results.append(result)

    return results


def get_available_models() -> list[str]:
    """Return list of configured LLM models."""
    return settings.llm_models
