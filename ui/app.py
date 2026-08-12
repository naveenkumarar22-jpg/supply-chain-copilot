import os
import uuid

import gradio as gr
import requests

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")


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
    response = requests.post(
        f"{API_URL}/query",
        json={"query": message, "session_id": session_id},
        timeout=60,
    )
    response.raise_for_status()
    return _format_response(response.json())


with gr.Blocks(title="Supply Chain Operations Copilot") as demo:
    session_id_state = gr.State(lambda: str(uuid.uuid4()))
    gr.ChatInterface(
        fn=respond,
        additional_inputs=[session_id_state],
        title="Supply Chain Operations Copilot",
        description=(
            "Ask about supplier delay risk, inventory risk, or company policy/SOP questions. "
            "All recommendations are advisory only -- human approval is required before any action."
        ),
    )

if __name__ == "__main__":
    demo.launch()
