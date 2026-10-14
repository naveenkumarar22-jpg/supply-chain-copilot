import sys
import time
import traceback
import uuid
from collections import defaultdict, deque
from pathlib import Path
from typing import Deque, Dict

# Running this file directly (`python ui/app.py`, or however HF Spaces
# invokes app_file) only puts this file's own directory on sys.path, not
# the repo root -- so core/, a sibling top-level package, wouldn't import.
# Insert the repo root explicitly, before importing anything from it.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gradio as gr

from core.orchestrator import run

try:
    import spaces
except ImportError:  # package not installed -- e.g. plain local dev without it
    spaces = None

if spaces is not None:
    # This app is CPU-only (it just calls the OpenAI API), but ZeroGPU
    # hardware refuses to start unless it detects at least one
    # @spaces.GPU-decorated function. This satisfies that platform
    # requirement only -- it's never called anywhere in the real request
    # flow (see respond() below), so actual behavior is unchanged.
    @spaces.GPU
    def _zerogpu_startup_probe() -> None:
        return None

# Cost/abuse safeguard for the public demo: a simple in-memory sliding-window
# limit, same idea as the FastAPI version from the Docker deployment path,
# just keyed on session_id instead of client IP since this standalone Gradio
# app has no separate HTTP layer to pull a request/IP from.
_RATE_LIMIT_WINDOW_SECONDS = 60
_RATE_LIMIT_MAX_REQUESTS = 10
_request_log: Dict[str, Deque[float]] = defaultdict(deque)


def _rate_limited(session_id: str) -> bool:
    now = time.time()
    timestamps = _request_log[session_id]
    while timestamps and timestamps[0] < now - _RATE_LIMIT_WINDOW_SECONDS:
        timestamps.popleft()
    if len(timestamps) >= _RATE_LIMIT_MAX_REQUESTS:
        return True
    timestamps.append(now)
    return False


def _format_response(data: dict) -> str:
    lines = [data["answer"], ""]
    lines.append(f"**Confidence:** {data['confidence']}")
    lines.append(f"**Reasoning:** {data['reasoning']}")
    if data["sources"]:
        lines.append("**Sources:**")
        lines.extend(f"- {s}" for s in data["sources"])
    if data["limitations"]:
        lines.append("**Limitations:**")
        lines.extend(f"- {item}" for item in data["limitations"])
    if data["next_steps"]:
        lines.append("**Next steps:**")
        lines.extend(f"- {item}" for item in data["next_steps"])
    return "\n".join(lines)


# Markers that identify an exhausted/limited OpenAI account, as they appear
# in the provider's error payload (core.llm_client re-raises it as the text
# of a RuntimeError, so substring matching is the available signal).
_QUOTA_MARKERS = ("insufficient_quota", "credit_balance_exhausted", "exceeded your current quota")
_RATE_LIMIT_MARKERS = ("rate_limit_exceeded", "429")


def _friendly_error(exc: Exception) -> str:
    detail = str(exc)
    if any(marker in detail for marker in _QUOTA_MARKERS):
        return (
            "⚠️ **This demo's OpenAI API quota is currently exhausted**, so the copilot can't "
            "answer right now. This is a billing limit on the demo account, not a fault in your "
            "question -- please check back later."
        )
    if any(marker in detail for marker in _RATE_LIMIT_MARKERS):
        return (
            "⚠️ **The demo is being rate limited by the model provider.** Please wait a moment "
            "and send your question again."
        )
    return (
        "⚠️ **Something went wrong handling that question.** The error has been logged. "
        "Please try again, or try one of the suggested prompts."
    )


def respond(message: str, history, session_id: str) -> str:
    if _rate_limited(session_id):
        return "Demo rate limit reached (10 messages/minute) -- please wait a minute and try again."
    try:
        response = run(query=message, session_id=session_id)
    except Exception as exc:
        # An uncaught exception reaches a visitor as Gradio's bare red "Error"
        # box -- no cause, indistinguishable from any other failure. Print the
        # traceback (it lands in the Space logs, where it's actually useful)
        # and return a readable explanation in the chat instead.
        traceback.print_exc()
        return _friendly_error(exc)
    return _format_response(response.model_dump())


with gr.Blocks(title="Supply Chain Operations Copilot") as demo:
    session_id_state = gr.State(lambda: str(uuid.uuid4()))
    gr.ChatInterface(
        fn=respond,
        additional_inputs=[session_id_state],
        title="Supply Chain Operations Copilot",
        description=(
            "🧪 **Portfolio demo** running on simulated sample data, not a real company's data. "
            "Limited to 10 messages/minute per visitor. "
            "Ask about supplier delay risk, inventory risk, or company policy/SOP questions. "
            "All recommendations are advisory only -- human approval is required before any action."
        ),
        # List of single-element lists (not flat strings): ChatInterface
        # requires list-of-lists when additional_inputs are present. Each
        # example only fills the message field -- it must never supply a
        # value for the session_id state, or clicking an example would
        # overwrite/collide a visitor's real session_id.
        examples=[
            ["Is supplier SKU-1042 at risk of delay?"],
            ["Are any of my parts likely to stock out?"],
            ["What's our escalation process when a tier-1 supplier is running late?"],
            ["Is that one still at risk of delay?"],
        ],
    )

if __name__ == "__main__":
    # 0.0.0.0 so the UI is reachable from outside the process (Docker, HF
    # Spaces, etc.) -- harmless for plain local runs too, since 0.0.0.0
    # still accepts connections via 127.0.0.1.
    demo.launch(server_name="0.0.0.0", server_port=7860)
