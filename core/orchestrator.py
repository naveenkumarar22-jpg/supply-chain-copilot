from core.io_contract import StructuredResponse
from core.llm_client import ask


def _run_intent(query: str, session_id: str) -> dict:
    # TODO(Phase 2): LLM-driven intent routing (Decision #2) — classify the
    # query into structured fields (intent, entity, args) instead of passing
    # the raw text straight through.
    return {"query": query, "session_id": session_id}


def _run_retrieval(context: dict) -> dict:
    # TODO(Phase 3): metadata-filtered retrieval over FAISS (Decision #4) —
    # pull relevant supplier/inventory/PO documents into the context here.
    context["retrieved_docs"] = []
    return context


def _run_tools(context: dict) -> dict:
    # TODO(Phase 4): tool registry dispatch (Decision #3) — call structured
    # tools keyed by intent/entity and fold their results into the context.
    context["tool_results"] = []
    return context


def _run_memory(context: dict) -> dict:
    # TODO(Phase 5): persistent, session-keyed memory (Decision #5) — load
    # and save session history here, keyed by context["session_id"].
    context["memory"] = []
    return context


def _run_safety(context: dict) -> dict:
    # TODO(Phase 6): suggest-only validation gate (Decision #10) — enforce
    # that the agent only proposes actions, never executes them.
    return context


def _final_answer(context: dict) -> StructuredResponse:
    answer_text = ask(context["query"])
    return StructuredResponse(
        answer=answer_text,
        reasoning="Direct LLM response; retrieval, tools, and memory are not wired in yet.",
        confidence="low",
        sources=[],
        limitations=["Phase 1 build: intent, retrieval, tools, memory, and safety stages are placeholders."],
        next_steps=["Wire up LLM-driven intent routing (Phase 2)."],
    )


def run(query: str, session_id: str) -> StructuredResponse:
    context = _run_intent(query, session_id)
    context = _run_retrieval(context)
    context = _run_tools(context)
    context = _run_memory(context)
    context = _run_safety(context)
    return _final_answer(context)
