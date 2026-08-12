from fastapi import FastAPI

from app.api.schemas import FeedbackRequest, FeedbackResponse, HealthResponse, QueryRequest
from core.intent import process as classify_intent
from core.io_contract import StructuredResponse
from core.orchestrator import run
from memory.session_memory import record_feedback

app = FastAPI(title="Supply Chain Operations Copilot")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/query", response_model=StructuredResponse)
def query(request: QueryRequest) -> StructuredResponse:
    return run(query=request.query, session_id=request.session_id)


@app.post("/feedback", response_model=FeedbackResponse)
def feedback(request: FeedbackRequest) -> FeedbackResponse:
    # Classify the query so this feedback is keyed to the same situational
    # entities (sku/tier/supplier) as Phase 5's tested flow -- not just a
    # bare, unkeyed session note.
    intent = classify_intent(request.query)
    record_feedback(
        session_id=request.session_id,
        query=request.query,
        instruction=request.instruction,
        intent=intent,
    )
    return FeedbackResponse(status="recorded")
