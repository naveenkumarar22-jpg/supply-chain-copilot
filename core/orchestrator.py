import json

from core.intent import process as classify_intent
from core.intent import route as route_intent
from core.io_contract import StructuredResponse
from core.llm_client import ask
from core.tools.registry import get_tool


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
    # Decision #3: look up the tool registered for this intent's route and
    # call it with the resolved intent — a plain registry lookup, no ad hoc
    # per-intent branching.
    tool = get_tool(context["route"])
    context["tool_result"] = tool(context["intent"]) if tool else None
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
    tool_result = context.get("tool_result")

    if tool_result is None:
        answer_text = ask(context["query"])
        return StructuredResponse(
            answer=answer_text,
            reasoning=(
                f"Classified intent: {intent.intent_type}. No tool is registered for this "
                "intent, so this is a direct LLM response with no grounding in data."
            ),
            confidence="low",
            sources=[],
            limitations=["No matching tool for this intent; retrieval, memory, and safety stages are placeholders."],
            next_steps=["Wire up metadata-filtered retrieval (Decision #4) for document-grounded answers."],
        )

    grounded_prompt = (
        "Answer the user's supply chain question using ONLY the structured data below. "
        "Be concise and specific.\n\n"
        f"Question: {context['query']}\n\n"
        f"Data: {json.dumps(tool_result, indent=2)}\n"
    )
    answer_text = ask(grounded_prompt)

    reasoning = " ".join(tool_result.get("reasoning", [])) or "See tool result."
    if tool_result.get("conflict_note"):
        reasoning += f" Conflicting signal: {tool_result['conflict_note']}"

    return StructuredResponse(
        answer=answer_text,
        reasoning=reasoning,
        confidence=tool_result.get("confidence", "low"),
        sources=[f"sample dataset ({tool_result['tool']} tool, sku={tool_result.get('sku')})"],
        limitations=["Retrieval, memory, and safety stages are placeholders."],
        next_steps=["Wire up metadata-filtered retrieval (Decision #4) for document-grounded answers."],
    )


def run(query: str, session_id: str) -> StructuredResponse:
    context = _run_intent(query, session_id)
    context = _run_retrieval(context)
    context = _run_tools(context)
    context = _run_memory(context)
    context = _run_safety(context)
    return _final_answer(context)
