from openai import OpenAI

from config.settings import settings

_client = OpenAI(api_key=settings.openai_api_key)


def ask(prompt: str) -> str:
    try:
        response = _client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except Exception as exc:
        raise RuntimeError(f"LLM call failed: {exc}") from exc
