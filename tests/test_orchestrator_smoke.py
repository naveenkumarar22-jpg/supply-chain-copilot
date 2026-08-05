from core.orchestrator import run

if __name__ == "__main__":
    response = run(
        query="Is supplier SKU-1042 at risk of delay?",
        session_id="demo-session",
    )
    print(response.model_dump_json(indent=2))
