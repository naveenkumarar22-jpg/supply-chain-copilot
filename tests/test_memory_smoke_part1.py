from core.orchestrator import run

SESSION_ID = "phase5-demo-session"

if __name__ == "__main__":
    print("=== Turn 1 ===")
    query1 = "Is supplier SKU-1042 at risk of delay?"
    r1 = run(query=query1, session_id=SESSION_ID)
    print(f"Query: {query1}")
    print(r1.model_dump_json(indent=2))

    print()
    print("=== Turn 2 (follow-up: 'that' should resolve to SKU-1042 via memory) ===")
    query2 = "Is that one still at risk of delay?"
    r2 = run(query=query2, session_id=SESSION_ID)
    print(f"Query: {query2}")
    print(r2.model_dump_json(indent=2))
