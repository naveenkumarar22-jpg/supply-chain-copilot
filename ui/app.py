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
    if response.status_code == 429:
        return response.json().get("detail", "Demo rate limit reached -- please wait a minute and try again.")
    response.raise_for_status()
    return _format_response(response.json())


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
    # 0.0.0.0 so the UI is reachable from outside the container (or any
    # non-localhost client) -- harmless for plain local runs too, since
    # 0.0.0.0 still accepts connections via 127.0.0.1.
    demo.launch(server_name="0.0.0.0", server_port=7860)
