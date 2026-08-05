import json
import re
from typing import Literal, Optional

from pydantic import BaseModel, ValidationError

from core.llm_client import ask

IntentType = Literal["supplier_delay_check", "inventory_risk_check", "unknown"]

_SKU_PATTERN = re.compile(r"\bSKU-\d+\b", re.IGNORECASE)
_REQUIRES_SKU = {"supplier_delay_check"}

_CLASSIFICATION_PROMPT = """You are an intent classifier for a supply chain operations copilot.

Classify the user's query into exactly one of these intent types:
- supplier_delay_check: the user asks whether a specific supplier or SKU is at risk of, or already experiencing, a delay.
- inventory_risk_check: the user asks about stock-out or inventory risk, generally or across items, not tied to one specific SKU.
- unknown: anything else -- small talk, unrelated topics, or queries that don't fit the above.

Also extract these arguments if present in the query, else use null:
- sku: a stock keeping unit identifier, e.g. "SKU-1042".
- supplier_id: a supplier identifier.

Respond with ONLY a JSON object in exactly this shape:
{{"intent_type": "...", "sku": ... or null, "supplier_id": ... or null}}

Query: "{query}"
"""


class Intent(BaseModel):
    intent_type: IntentType
    sku: Optional[str] = None
    supplier_id: Optional[str] = None
    sku_resolved: bool = True


def classify(query: str) -> Intent:
    raw = ask(_CLASSIFICATION_PROMPT.format(query=query), json_mode=True)
    payload = _extract_json(raw)
    try:
        return Intent(
            intent_type=payload.get("intent_type", "unknown"),
            sku=payload.get("sku"),
            supplier_id=payload.get("supplier_id"),
        )
    except ValidationError:
        return Intent(intent_type="unknown")


def _extract_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if "\n" in text:
            text = text.split("\n", 1)[1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def resolve_sku(intent: Intent, query: str) -> Intent:
    if intent.intent_type not in _REQUIRES_SKU:
        intent.sku_resolved = True
        return intent
    if intent.sku:
        intent.sku_resolved = True
        return intent
    match = _SKU_PATTERN.search(query)
    if match:
        intent.sku = match.group(0).upper()
        intent.sku_resolved = True
    else:
        intent.sku_resolved = False
    return intent


def route(intent: Intent) -> str:
    # Deterministic dispatch: a plain lookup on the LLM's classified
    # intent_type, not keyword-matching on the raw query text.
    # TODO(Phase 3): point these at real tool-registry entries (Decision #3).
    routes = {
        "supplier_delay_check": "supplier_delay_tool",
        "inventory_risk_check": "inventory_risk_tool",
        "unknown": "no_tool",
    }
    return routes.get(intent.intent_type, "no_tool")


def process(query: str) -> Intent:
    intent = classify(query)
    return resolve_sku(intent, query)
