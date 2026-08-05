from core.intent import process as classify_intent
from core.orchestrator import run

SAMPLE_QUERIES = [
    "Is supplier SKU-1042 at risk of delay?",
    "Are any of my parts likely to stock out?",
    "What's the weather today?",
]

if __name__ == "__main__":
    for query in SAMPLE_QUERIES:
        intent = classify_intent(query)
        print(f"Query: {query}")
        print(f"  intent_type   = {intent.intent_type}")
        print(f"  sku           = {intent.sku}")
        print(f"  supplier_id   = {intent.supplier_id}")
        print(f"  sku_resolved  = {intent.sku_resolved}")

        response = run(query=query, session_id="demo-session")
        print(f"  orchestrator.reasoning = {response.reasoning}")
        print()
