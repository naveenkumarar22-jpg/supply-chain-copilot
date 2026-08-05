from core.orchestrator import run

SAMPLE_QUERIES = [
    "Is supplier SKU-1042 at risk of delay?",
    "Are any of my parts likely to stock out?",
]

if __name__ == "__main__":
    for query in SAMPLE_QUERIES:
        response = run(query=query, session_id="demo-session")
        print(f"Query: {query}")
        print(response.model_dump_json(indent=2))
        print()
