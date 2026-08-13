import sys
import time
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


def respond(message: str, history, session_id: str) -> str:
    if _rate_limited(session_id):
        return "Demo rate limit reached (10 messages/minute) -- please wait a minute and try again."
    response = run(query=message, session_id=session_id)
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
    )

if __name__ == "__main__":
    # 0.0.0.0 so the UI is reachable from outside the process (Docker, HF
    # Spaces, etc.) -- harmless for plain local runs too, since 0.0.0.0
    # still accepts connections via 127.0.0.1.
    demo.launch(server_name="0.0.0.0", server_port=7860)
