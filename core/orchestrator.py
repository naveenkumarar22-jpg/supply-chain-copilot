from core.intent import process as classify_intent
from core.intent import route as route_intent
from core.io_contract import StructuredResponse
from core.llm_client import ask


def _run_intent(query: str, session_id: str) -> dict:
    # Decision #2: the LLM classifies the query into structured fields
    # (core.intent.classify), and plain Python dispatches on the result
    # (core.intent.route) — no keyword if/elif on the raw text.
    # Decision #9: dual-source sku resolution (LLM value, then regex
    # fallback, else marked unresolved) happens inside classify_intent.
    intent = classify_intent(query)
    return {
        "query": query,
        "session_id": session_id,
        "intent": intent,
        "route": route_intent(intent),
    }


def _run_retrieval(context: dict) -> dict:
    # TODO(later phase): metadata-filtered retrieval over FAISS (Decision #4)
    # — pull relevant supplier/inventory/PO documents into the context here.
    context["retrieved_docs"] = []
    return context


def _run_tools(context: dict) -> dict:
    # TODO(Phase 3): tool registry dispatch (Decision #3) — call the tool
    # named by context["route"], keyed by intent/entity, and fold its
    # results into the context.
    context["tool_results"] = []
    return context


def _run_memory(context: dict) -> dict:
    # TODO(later phase): persistent, session-keyed memory (Decision #5) —
    # load and save session history here, keyed by context["session_id"].
    context["memory"] = []
    return context


def _run_safety(context: dict) -> dict:
    # TODO(later phase): suggest-only validation gate (Decision #10) —
    # enforce that the agent only proposes actions, never executes them.
    return context


def _final_answer(context: dict) -> StructuredResponse:
    intent = context["intent"]
    answer_text = ask(context["query"])
    return StructuredResponse(
        answer=answer_text,
        reasoning=(
            f"Classified intent: {intent.intent_type} (sku={intent.sku!r}, "
            f"sku_resolved={intent.sku_resolved}). Retrieval, tools, and "
            "memory are not wired in yet."
        ),
        confidence="low",
        sources=[],
        limitations=["Phase 2 build: retrieval, tools, memory, and safety stages are placeholders."],
        next_steps=["Wire up the tool registry for the routed intent (Phase 3)."],
    )


def run(query: str, session_id: str) -> StructuredResponse:
    context = _run_intent(query, session_id)
    context = _run_retrieval(context)
    context = _run_tools(context)
    context = _run_memory(context)
    context = _run_safety(context)
    return _final_answer(context)
