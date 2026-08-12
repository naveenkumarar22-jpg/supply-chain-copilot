from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    session_id: str


class FeedbackRequest(BaseModel):
    session_id: str
    query: str
    instruction: str


class FeedbackResponse(BaseModel):
    status: str


class HealthResponse(BaseModel):
    status: str
