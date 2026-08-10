from core.orchestrator import run

if __name__ == "__main__":
    query = "Is supplier SKU-1042 at risk of delay?"
    response = run(
        query=query,
        session_id="demo-session",
    )
    print(f"Query: {query}")
    print(response.model_dump_json(indent=2))
