from typing import List, Optional

from memory import store


def recall_recent_turns(session_id: str, limit: int = 5) -> List[dict]:
    return store.load_recent_turns(session_id, limit=limit)


def format_memory_context(recent_turns: List[dict]) -> str:
    if not recent_turns:
        return "(none)"
    lines = [
        f"- query: {turn['query']!r} -> intent={turn['intent_type']}, sku={turn['sku']}, "
        f"criticality_tier={turn['criticality_tier']}, supplier_id={turn['supplier_id']}"
        for turn in recent_turns
    ]
    return "\n".join(lines)


def relevant_feedback(session_id: str, intent) -> List[dict]:
    return store.load_relevant_feedback(
        session_id,
        intent_type=intent.intent_type,
        sku=intent.sku,
        criticality_tier=intent.criticality_tier,
        supplier_id=intent.supplier_id,
    )


def persist_turn(session_id: str, query: str, intent, response) -> None:
    store.save_turn(
        session_id=session_id,
        query=query,
        intent_type=intent.intent_type,
        sku=intent.sku,
        criticality_tier=intent.criticality_tier,
        supplier_id=intent.supplier_id,
        response_json=response.model_dump_json(),
    )


def record_feedback(session_id: str, query: str, instruction: str, intent: Optional[object] = None) -> None:
    store.save_feedback(
        session_id=session_id,
        query=query,
        intent_type=getattr(intent, "intent_type", None),
        sku=getattr(intent, "sku", None),
        criticality_tier=getattr(intent, "criticality_tier", None),
        supplier_id=getattr(intent, "supplier_id", None),
        instruction=instruction,
    )
