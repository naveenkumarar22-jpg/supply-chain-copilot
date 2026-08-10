from core.intent import process as classify_intent
from core.orchestrator import run
from memory import session_memory, store

SESSION_ID = "phase5-demo-session"

if __name__ == "__main__":
    print("=== Confirming history persisted across process restart ===")
    turns = store.load_recent_turns(SESSION_ID, limit=10)
    for t in turns:
        print(f"- query={t['query']!r} intent={t['intent_type']} sku={t['sku']}")
    assert len(turns) >= 2, "expected at least the 2 turns from part 1 to be persisted"
    print(f"OK: {len(turns)} turn(s) found in a fresh process.")

    print()
    print("=== Recording feedback tied to SKU-1042 ===")
    feedback_query = "Is supplier SKU-1042 at risk of delay?"
    feedback_intent = classify_intent(feedback_query)
    session_memory.record_feedback(
        session_id=SESSION_ID,
        query=feedback_query,
        instruction=(
            "For SKU-1042, always flag that the backup supplier is dual-sourced only on "
            "paper -- it has never actually shipped a unit."
        ),
        intent=feedback_intent,
    )
    print("Feedback recorded.")

    print()
    print("=== Turn 3: a related (not verbatim) query about the same SKU ===")
    query3 = "Any update on the delay situation for SKU-1042?"
    intent3 = classify_intent(query3)
    matched = session_memory.relevant_feedback(SESSION_ID, intent3)
    print(f"Matched {len(matched)} feedback entr(ies) for this situation (explicit check):")
    for m in matched:
        print(f"  - {m['instruction']}")

    r3 = run(query=query3, session_id=SESSION_ID)
    print()
    print(f"Query: {query3}")
    print(r3.model_dump_json(indent=2))
