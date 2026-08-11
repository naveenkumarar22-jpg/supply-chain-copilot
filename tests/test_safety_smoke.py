from core.io_contract import StructuredResponse
from core.orchestrator import run
from core.safety import enforce_suggest_only

if __name__ == "__main__":
    print("=== Case 1: normal query passes through, gate adds advisory notice ===")
    query = "Is supplier SKU-1042 at risk of delay?"
    response = run(query=query, session_id="phase6-demo-session")
    print(f"Query: {query}")
    print(response.model_dump_json(indent=2))

    print()
    print("=== Case 2: direct unit test -- crafted response claims an executed action ===")
    crafted = StructuredResponse(
        answer=(
            "I've placed the reorder for SKU-1002 with Acme Components. "
            "Separately, the PO for SKU-1023 has been cancelled due to the ongoing delay."
        ),
        reasoning="Crafted for testing -- these action claims did not come from a real tool.",
        confidence="high",
        sources=["test fixture"],
        limitations=[],
        next_steps=[],
    )
    gated = enforce_suggest_only(crafted)
    print(gated.model_dump_json(indent=2))
