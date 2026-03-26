"""
Query Intelligence service.
Performs intent detection, entity extraction, and schema mapping
to optimize query processing.
"""

import re
import logging
from backend.services.llm_service import generate_response
from backend.services.neo4j_service import get_schema

logger = logging.getLogger(__name__)

# ── Intent Categories ─────────────────────────────────────────
INTENTS = {
    "aggregate": ["top", "total", "sum", "average", "count", "most", "least", "highest", "lowest", "max", "min"],
    "lookup": ["who", "what", "which", "find", "show", "get", "list", "tell"],
    "comparison": ["compare", "versus", "vs", "difference", "between", "better", "worse"],
    "trend": ["over time", "trend", "growth", "decline", "change", "year", "month", "quarterly"],
    "relationship": ["connected", "related", "linked", "bought", "ordered", "placed", "contains"],
}

# ── Entity Patterns ───────────────────────────────────────────
ENTITY_MAP = {
    "customer": {"label": "Customer", "props": ["customer_name", "segment", "region", "country"]},
    "product": {"label": "Product", "props": ["product_name", "category", "supplier", "unit_price"]},
    "order": {"label": "Order", "props": ["order_id", "quantity", "sales_amount", "order_year", "order_month"]},
}


def detect_intent(query: str) -> str:
    """Detect the primary intent of a natural language query."""
    query_lower = query.lower()

    scores = {}
    for intent, keywords in INTENTS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > 0:
            scores[intent] = score

    if scores:
        return max(scores, key=scores.get)
    return "lookup"  # default


def extract_entities(query: str) -> list[dict]:
    """Extract entities mentioned in the query and map to graph schema."""
    query_lower = query.lower()
    found = []

    for entity_key, entity_info in ENTITY_MAP.items():
        # Check for entity type mentions
        if entity_key in query_lower or entity_info["label"].lower() in query_lower:
            found.append({
                "entity": entity_info["label"],
                "properties": entity_info["props"],
            })

        # Check for specific property mentions
        for prop in entity_info["props"]:
            clean_prop = prop.replace("_", " ")
            if clean_prop in query_lower:
                if not any(e["entity"] == entity_info["label"] for e in found):
                    found.append({
                        "entity": entity_info["label"],
                        "properties": entity_info["props"],
                        "matched_property": prop,
                    })

    return found


def extract_numeric_constraints(query: str) -> dict:
    """Extract numeric values and constraints from the query."""
    constraints = {}

    # Top N pattern
    top_match = re.search(r"top\s+(\d+)", query.lower())
    if top_match:
        constraints["limit"] = int(top_match.group(1))

    # Year pattern
    year_match = re.search(r"(20\d{2})", query)
    if year_match:
        constraints["year"] = int(year_match.group(1))

    # Price/amount patterns
    amount_match = re.search(r"(?:above|over|more than|greater than)\s+\$?(\d+\.?\d*)", query.lower())
    if amount_match:
        constraints["min_amount"] = float(amount_match.group(1))

    amount_match2 = re.search(r"(?:below|under|less than)\s+\$?(\d+\.?\d*)", query.lower())
    if amount_match2:
        constraints["max_amount"] = float(amount_match2.group(1))

    return constraints


def analyze_query(query: str) -> dict:
    """
    Full query intelligence analysis.
    Returns intent, entities, constraints, and suggested approach.
    """
    intent = detect_intent(query)
    entities = extract_entities(query)
    constraints = extract_numeric_constraints(query)

    # Determine if RAG would help
    use_rag = intent in ["lookup", "comparison"] or not entities

    # Determine complexity
    complexity = "simple"
    if len(entities) > 1 or intent == "trend":
        complexity = "complex"
    if constraints:
        complexity = "moderate" if complexity == "simple" else "complex"

    return {
        "intent": intent,
        "entities": entities,
        "constraints": constraints,
        "use_rag": use_rag,
        "complexity": complexity,
        "schema": get_schema(),
    }


def optimize_query_prompt(query: str, analysis: dict) -> str:
    """
    Build an optimized prompt for Cypher generation based on query analysis.
    """
    prompt_parts = [f"User question: {query}"]

    if analysis["entities"]:
        entities_str = ", ".join(e["entity"] for e in analysis["entities"])
        prompt_parts.append(f"Relevant graph entities: {entities_str}")

    if analysis["constraints"]:
        prompt_parts.append(f"Constraints: {analysis['constraints']}")

    prompt_parts.append(f"Query intent: {analysis['intent']}")
    prompt_parts.append(f"Graph schema: {analysis['schema']}")

    return "\n".join(prompt_parts)
