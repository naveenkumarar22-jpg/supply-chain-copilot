from typing import Optional

from openai import OpenAI

from config.settings import settings

_client = OpenAI(api_key=settings.openai_api_key)


def ask(prompt: str, json_mode: bool = False, temperature: Optional[float] = None, max_tokens: int = 500) -> str:
    try:
        response = _client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"} if json_mode else None,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as exc:
        raise RuntimeError(f"LLM call failed: {exc}") from exc
