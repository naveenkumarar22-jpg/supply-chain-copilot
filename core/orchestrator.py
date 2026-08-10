import json

from core.intent import process as classify_intent
from core.intent import route as route_intent
from core.io_contract import StructuredResponse
from core.llm_client import ask
from core.tools.registry import get_tool
from memory import session_memory
from retrieval.retriever import retrieve


def _run_memory_recall(context: dict) -> dict:
    # Decision #5: load this session's recent turns BEFORE intent
    # classification runs -- a follow-up like "is that one critical?" can
    # only resolve "that" to a prior SKU if the classifier sees the history.
    recent_turns = session_memory.recall_recent_turns(context["session_id"])
    context["recent_turns"] = recent_turns
    context["memory_context"] = session_memory.format_memory_context(recent_turns)
    return context


def _run_intent(context: dict) -> dict:
    # Decision #2: the LLM classifies the query into structured fields
    # (core.intent.classify), and plain Python dispatches on the result
    # (core.intent.route) — no keyword if/elif on the raw text.
    # Decision #9: dual-source sku resolution (LLM value, then regex
    # fallback, else marked unresolved) happens inside classify_intent.
    intent = classify_intent(context["query"], memory_context=context.get("memory_context"))
    context["intent"] = intent
    context["route"] = route_intent(intent)
    # Decision #6: now that the intent's entities are known, pull feedback
    # keyed on the SITUATION (matching sku/tier/supplier/intent_type), not
    # on exact past query text.
    context["relevant_feedback"] = session_memory.relevant_feedback(context["session_id"], intent)
    return context


def _run_retrieval(context: dict) -> dict:
    # Decision #4: metadata-filtered retrieval only runs for policy_lookup
    # intents -- other intents are grounded by a structured tool instead
    # (see _run_tools), so there's nothing to retrieve for them.
    intent = context["intent"]
    if intent.intent_type != "policy_lookup":
        context["retrieved_docs"] = []
        return context

    metadata_filter = {"criticality_tier": intent.criticality_tier} if intent.criticality_tier else None
    context["retrieved_docs"] = retrieve(context["query"], metadata_filter=metadata_filter)
    return context


def _run_tools(context: dict) -> dict:
    # Decision #3: look up the tool registered for this intent's route and
    # call it with the resolved intent — a plain registry lookup, no ad hoc
    # per-intent branching.
    tool = get_tool(context["route"])
    context["tool_result"] = tool(context["intent"]) if tool else None
    return context


def _run_safety(context: dict) -> dict:
    # TODO(later phase): suggest-only validation gate (Decision #10) —
    # enforce that the agent only proposes actions, never executes them.
    return context


def _final_answer(context: dict) -> StructuredResponse:
    tool_result = context.get("tool_result")
    retrieved_docs = context.get("retrieved_docs") or []

    if tool_result is not None:
        return _answer_from_tool(context, tool_result)
    if retrieved_docs:
        return _answer_from_retrieval(context, retrieved_docs)
    return _answer_ungrounded(context)


def _feedback_block(context: dict) -> str:
    # Decision #6: fold any situationally-relevant feedback into the prompt
    # and let the LLM interpret what it implies for this answer -- rather
    # than a hardcoded find-and-replace on exact past query text.
    feedback = context.get("relevant_feedback") or []
    if not feedback:
        return ""
    lines = "\n".join(f"- {row['instruction']}" for row in feedback)
    return (
        "\n\nPrior feedback from this session that may apply to this question "
        f"-- apply it if relevant, ignore it if not:\n{lines}\n"
    )


def _answer_ungrounded(context: dict) -> StructuredResponse:
    intent = context["intent"]
    answer_text = ask(context["query"] + _feedback_block(context))
    return StructuredResponse(
        answer=answer_text,
        reasoning=(
            f"Classified intent: {intent.intent_type}. No tool or retrieved document "
            "applies, so this is a direct LLM response with no grounding in data."
        ),
        confidence="low",
        sources=[],
        limitations=["No matching tool or document for this intent; safety stage is a placeholder."],
        next_steps=["Wire up the suggest-only safety gate (Decision #10)."],
    )


def _answer_from_tool(context: dict, tool_result: dict) -> StructuredResponse:
    grounded_prompt = (
        "Answer the user's supply chain question using ONLY the structured data below. "
        "Be concise and specific.\n\n"
        f"Question: {context['query']}\n\n"
        f"Data: {json.dumps(tool_result, indent=2)}\n"
        f"{_feedback_block(context)}"
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
        limitations=["Safety stage is a placeholder."],
        next_steps=["Wire up the suggest-only safety gate (Decision #10)."],
    )


def _answer_from_retrieval(context: dict, retrieved_docs: list) -> StructuredResponse:
    context_block = "\n\n".join(f"[{doc['id']}] {doc['text']}" for doc in retrieved_docs)
    grounded_prompt = (
        "Answer the user's supply chain question using ONLY the document excerpts below. "
        "Cite which document id(s) support your answer. If the excerpts don't answer the "
        "question, say so plainly rather than guessing.\n\n"
        f"Question: {context['query']}\n\n"
        f"Documents:\n{context_block}\n"
        f"{_feedback_block(context)}"
    )
    answer_text = ask(grounded_prompt)

    return StructuredResponse(
        answer=answer_text,
        reasoning=f"Retrieved {len(retrieved_docs)} document chunk(s) via metadata-filtered semantic search.",
        confidence="high",
        sources=[f"{doc['id']} ({doc['metadata']['doc_type']}: {doc['metadata']['topic']})" for doc in retrieved_docs],
        limitations=["Safety stage is a placeholder."],
        next_steps=["Wire up the suggest-only safety gate (Decision #10)."],
    )


def run(query: str, session_id: str) -> StructuredResponse:
    context = {"query": query, "session_id": session_id}
    context = _run_memory_recall(context)
    context = _run_intent(context)
    context = _run_retrieval(context)
    context = _run_tools(context)
    context = _run_safety(context)
    response = _final_answer(context)
    session_memory.persist_turn(session_id, query, context["intent"], response)
    return response
