from typing import List

from pydantic import BaseModel


class StructuredResponse(BaseModel):
    answer: str
    reasoning: str
    confidence: str
    sources: List[str]
    limitations: List[str]
    next_steps: List[str]
