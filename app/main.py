import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import FastAPI, HTTPException, Request

from app.api.schemas import FeedbackRequest, FeedbackResponse, HealthResponse, QueryRequest
from core.intent import process as classify_intent
from core.io_contract import StructuredResponse
from core.orchestrator import run
from memory.session_memory import record_feedback

app = FastAPI(title="Supply Chain Operations Copilot")

# Cost/abuse safeguard for the public demo deployment: a simple in-memory,
# per-client-IP sliding-window limit on the two LLM-backed endpoints. No
# external dependency, no persistence needed -- this only has to survive
# for the lifetime of one running process.
_RATE_LIMIT_WINDOW_SECONDS = 60
_RATE_LIMIT_MAX_REQUESTS = 10
_request_log: Dict[str, Deque[float]] = defaultdict(deque)


def _enforce_rate_limit(client_ip: str) -> None:
    now = time.time()
    timestamps = _request_log[client_ip]
    while timestamps and timestamps[0] < now - _RATE_LIMIT_WINDOW_SECONDS:
        timestamps.popleft()
    if len(timestamps) >= _RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Demo rate limit reached (10 requests/minute per visitor) -- please wait a minute and try again.",
        )
    timestamps.append(now)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/query", response_model=StructuredResponse)
def query(request: QueryRequest, http_request: Request) -> StructuredResponse:
    _enforce_rate_limit(http_request.client.host)
    return run(query=request.query, session_id=request.session_id)


@app.post("/feedback", response_model=FeedbackResponse)
def feedback(request: FeedbackRequest, http_request: Request) -> FeedbackResponse:
    _enforce_rate_limit(http_request.client.host)
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
