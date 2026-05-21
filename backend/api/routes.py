"""FastAPI routes for Athena research API."""

import logging
import time
import uuid
from collections import defaultdict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.graph.builder import graph
from backend.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

# In-memory rate limiter (local dev only)
_rate_limits: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(user_id: str = "local_user") -> None:
    """Simple sliding window rate limiter."""
    now = time.time()
    window = settings.RATE_LIMIT_WINDOW
    max_requests = settings.RATE_LIMIT_MAX_REQUESTS

    # Clean old entries
    _rate_limits[user_id] = [
        t for t in _rate_limits[user_id] if now - t < window
    ]

    if len(_rate_limits[user_id]) >= max_requests:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {max_requests} requests per {window}s.",
        )

    _rate_limits[user_id].append(now)


# --- Request/Response Models ---

class ResearchStartRequest(BaseModel):
    company: str


class ResearchStartResponse(BaseModel):
    job_id: str
    status: str
    plan: list[str]


class ApproveResponse(BaseModel):
    status: str


class StatusResponse(BaseModel):
    job_id: str
    status: str
    current_node: str | None
    plan: list[str]
    company: str


class ReportResponse(BaseModel):
    job_id: str
    status: str
    report: str | None


# --- Routes ---

@router.post("/research/start", response_model=ResearchStartResponse)
async def start_research(req: ResearchStartRequest):
    """Start a new research job. Runs planner and pauses for approval."""
    _check_rate_limit()

    company = req.company.strip()
    if not company:
        raise HTTPException(status_code=400, detail="Company name is required")

    job_id = str(uuid.uuid4())
    thread = {"configurable": {"thread_id": job_id}}

    logger.info(f"Starting research job {job_id} for '{company}'")

    # Run graph until interrupt (pauses before scraper_dispatch)
    try:
        result = await graph.ainvoke(
            {"company": company},
            config=thread,
        )
    except Exception as e:
        # Graph interrupted at checkpoint — this is expected
        logger.debug(f"Graph paused at checkpoint: {e}")

    # Get current state to retrieve the plan
    state = await graph.aget_state(thread)
    plan = state.values.get("plan", [])

    return ResearchStartResponse(
        job_id=job_id,
        status="awaiting_approval",
        plan=plan,
    )


@router.post("/research/{job_id}/approve", response_model=ApproveResponse)
async def approve_plan(job_id: str):
    """Approve the research plan and resume the graph."""
    thread = {"configurable": {"thread_id": job_id}}

    # Verify job exists
    state = await graph.aget_state(thread)
    if not state.values:
        raise HTTPException(status_code=404, detail="Job not found")

    logger.info(f"Plan approved for job {job_id}")

    # Mark the plan approved. The WebSocket endpoint drives the graph
    # forward via astream_events(None, ...); running ainvoke here too
    # would double-execute the graph and block this request for minutes.
    await graph.aupdate_state(thread, {"plan_approved": True})

    return ApproveResponse(status="approved")


@router.get("/research/{job_id}/status", response_model=StatusResponse)
async def get_status(job_id: str):
    """Get current status of a research job."""
    thread = {"configurable": {"thread_id": job_id}}

    state = await graph.aget_state(thread)
    if not state.values:
        raise HTTPException(status_code=404, detail="Job not found")

    values = state.values
    next_nodes = state.next

    # Determine status. "completed" requires an actual final_report —
    # next_nodes can be transiently empty between checkpoints while the
    # graph is still running, so we can't infer completion from it.
    if values.get("final_report"):
        status = "completed"
    elif next_nodes and "scraper_dispatch" in next_nodes:
        status = "awaiting_approval"
    else:
        status = "running"

    current_node = next_nodes[0] if next_nodes else None

    return StatusResponse(
        job_id=job_id,
        status=status,
        current_node=current_node,
        plan=values.get("plan", []),
        company=values.get("company", ""),
    )


@router.get("/research/{job_id}/report", response_model=ReportResponse)
async def get_report(job_id: str):
    """Get the final report for a completed research job."""
    thread = {"configurable": {"thread_id": job_id}}

    state = await graph.aget_state(thread)
    if not state.values:
        raise HTTPException(status_code=404, detail="Job not found")

    report = state.values.get("final_report")
    status = "completed" if report else "in_progress"

    return ReportResponse(
        job_id=job_id,
        status=status,
        report=report,
    )
