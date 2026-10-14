import sqlite3
import sys
from typing import Callable, List, Optional, TypeVar

from memory import store

T = TypeVar("T")


def _safe(operation: str, call: Callable[[], T], fallback: T) -> T:
    # Session memory is an enhancement, not a precondition for answering:
    # if the SQLite file is unwritable (a read-only container filesystem, a
    # full disk, an ephemeral Space whose storage went away mid-request),
    # the copilot should still answer -- just without conversational recall.
    # Failing loudly to the logs but softly to the user is the right trade
    # here, since the alternative is a dead request for a healthy pipeline.
    try:
        return call()
    except (sqlite3.Error, OSError) as exc:
        print(
            f"[memory] {operation} failed: {exc} -- continuing without session memory",
            file=sys.stderr,
            flush=True,
        )
        return fallback


def recall_recent_turns(session_id: str, limit: int = 5) -> List[dict]:
    return _safe(
        "recall_recent_turns",
        lambda: store.load_recent_turns(session_id, limit=limit),
        fallback=[],
    )


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
    return _safe(
        "relevant_feedback",
        lambda: store.load_relevant_feedback(
            session_id,
            intent_type=intent.intent_type,
            sku=intent.sku,
            criticality_tier=intent.criticality_tier,
            supplier_id=intent.supplier_id,
        ),
        fallback=[],
    )


def persist_turn(session_id: str, query: str, intent, response) -> None:
    _safe(
        "persist_turn",
        lambda: store.save_turn(
            session_id=session_id,
            query=query,
            intent_type=intent.intent_type,
            sku=intent.sku,
            criticality_tier=intent.criticality_tier,
            supplier_id=intent.supplier_id,
            response_json=response.model_dump_json(),
        ),
        fallback=None,
    )


def record_feedback(session_id: str, query: str, instruction: str, intent: Optional[object] = None) -> None:
    _safe(
        "record_feedback",
        lambda: store.save_feedback(
            session_id=session_id,
            query=query,
            intent_type=getattr(intent, "intent_type", None),
            sku=getattr(intent, "sku", None),
            criticality_tier=getattr(intent, "criticality_tier", None),
            supplier_id=getattr(intent, "supplier_id", None),
            instruction=instruction,
        ),
        fallback=None,
    )
