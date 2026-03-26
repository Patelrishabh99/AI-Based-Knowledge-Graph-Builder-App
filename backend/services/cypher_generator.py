"""
Cypher Query Generator.
Uses LangChain's GraphCypherQAChain for NL → Cypher conversion,
with schema-aware generation and query validation.
"""

import logging
from typing import Optional
from langchain_neo4j import GraphCypherQAChain
from backend.config import get_settings
from backend.services.neo4j_service import get_graph
from backend.services.llm_service import get_llm

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Cached chain ──────────────────────────────────────────────
_chain = None


def get_chain(model_name: Optional[str] = None):
    """Get or create the GraphCypherQAChain."""
    global _chain
    if _chain is None or model_name:
        llm = get_llm(model_name)
        graph = get_graph()
        _chain = GraphCypherQAChain.from_llm(
            llm=llm,
            graph=graph,
            verbose=False,
            allow_dangerous_requests=True,
            return_intermediate_steps=True,
        )
    return _chain


def generate_cypher(query: str, model_name: Optional[str] = None) -> dict:
    """
    Convert natural language query to Cypher, execute, and return results.

    Returns:
        dict with keys: cypher, raw_results, answer
    """
    chain = get_chain(model_name)

    try:
        response = chain.invoke({"query": query})

        # Extract intermediate steps (Cypher query and raw results)
        cypher_query = ""
        raw_results = []

        if "intermediate_steps" in response:
            steps = response["intermediate_steps"]
            if len(steps) > 0:
                cypher_query = steps[0].get("query", "") if isinstance(steps[0], dict) else str(steps[0])
            if len(steps) > 1:
                raw_results = steps[1].get("context", []) if isinstance(steps[1], dict) else steps[1]
                if isinstance(raw_results, str):
                    raw_results = [{"result": raw_results}]

        answer = response.get("result", "")

        return {
            "cypher": cypher_query,
            "raw_results": raw_results if isinstance(raw_results, list) else [raw_results],
            "answer": answer,
        }
    except Exception as e:
        logger.error("Cypher generation error: %s", e)
        return {
            "cypher": "",
            "raw_results": [],
            "answer": f"Error generating query: {str(e)}",
            "error": str(e),
        }


def validate_cypher(cypher: str) -> bool:
    """Basic Cypher query validation."""
    if not cypher or not cypher.strip():
        return False

    # Check for dangerous operations
    dangerous = ["DROP", "DELETE", "DETACH DELETE", "CREATE INDEX", "DROP INDEX"]
    upper = cypher.upper()
    for op in dangerous:
        if op in upper and "RETURN" not in upper:
            return False

    return True


def explain_cypher(cypher: str) -> str:
    """Use LLM to explain a Cypher query in plain English."""
    from backend.services.llm_service import generate_response
    result = generate_response(
        query=f"Explain this Cypher query in simple terms:\n{cypher}",
        system_prompt="You are a Neo4j database expert. Explain Cypher queries in plain English, briefly.",
    )
    return result["answer"]
