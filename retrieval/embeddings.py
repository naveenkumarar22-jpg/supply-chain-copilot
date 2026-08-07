from typing import List

from openai import OpenAI

from config.settings import settings

_client = OpenAI(api_key=settings.openai_api_key)


def embed(text: str) -> List[float]:
    try:
        response = _client.embeddings.create(
            model=settings.openai_embedding_model,
            input=text,
        )
        return response.data[0].embedding
    except Exception as exc:
        raise RuntimeError(f"Embedding call failed: {exc}") from exc
