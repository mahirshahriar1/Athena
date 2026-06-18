"""FastAPI routes for Athena research API."""

import asyncio
import logging
import time
import uuid
from collections import defaultdict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.graph.builder import graph
from backend.core.config import settings
from backend.core.tokens import TokenTracker, get_token_totals
from backend.core import db
from backend.nodes.comparator import run_comparator

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
    website_url: str | None = None


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


class TokenUsage(BaseModel):
    input: int
    output: int
    total: int
    calls: int


class ReportResponse(BaseModel):
    job_id: str
    status: str
    report: str | None
    tokens: TokenUsage | None = None


# --- Routes ---

@router.post("/research/start", response_model=ResearchStartResponse)
async def start_research(req: ResearchStartRequest):
    """Start a new research job. Runs planner and pauses for approval."""
    _check_rate_limit()

    company = req.company.strip()
    if not company:
        raise HTTPException(status_code=400, detail="Company name is required")

    seed_url = (req.website_url or "").strip() or None
    if seed_url and not seed_url.startswith(("http://", "https://")):
        seed_url = f"https://{seed_url}"

    job_id = str(uuid.uuid4())
    tracker = TokenTracker(job_id)
    thread = {
        "configurable": {"thread_id": job_id},
        "callbacks": [tracker],
    }

    logger.info(f"Starting research job {job_id} for '{company}' (seed_url={seed_url})")

    # Run graph until interrupt (pauses before scraper_dispatch)
    try:
        result = await graph.ainvoke(
            {"company": company, "seed_url": seed_url},
            config=thread,
        )
    except Exception as e:
        # Graph interrupted at checkpoint — this is expected
        logger.debug(f"Graph paused at checkpoint: {e}")

    # Get current state to retrieve the plan
    state = await graph.aget_state(thread)
    plan = state.values.get("plan", [])

    # Persist initial row so the run shows up in history immediately
    db.insert_job(job_id=job_id, company=company, seed_url=seed_url, plan=plan)

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
    db.update_status(job_id, "running")

    return ApproveResponse(status="approved")


@router.get("/research/{job_id}/status", response_model=StatusResponse)
async def get_status(job_id: str):
    """Get current status of a research job (single or comparison)."""
    thread = {"configurable": {"thread_id": job_id}}
    state = await graph.aget_state(thread)

    # Single-research path: state present in MemorySaver
    if state.values:
        values = state.values
        next_nodes = state.next
        if values.get("final_report"):
            status = "completed"
        elif next_nodes and "scraper_dispatch" in next_nodes:
            status = "awaiting_approval"
        else:
            status = "running"
        return StatusResponse(
            job_id=job_id,
            status=status,
            current_node=next_nodes[0] if next_nodes else None,
            plan=values.get("plan", []),
            company=values.get("company", ""),
        )

    # Comparison path (or post-restart): look up in SQLite
    persisted = db.get_job(job_id)
    if not persisted:
        raise HTTPException(status_code=404, detail="Job not found")

    return StatusResponse(
        job_id=job_id,
        status=persisted["status"],
        current_node=None,
        plan=persisted.get("plan", []),
        company=persisted["company"],
    )


@router.get("/research/{job_id}/report", response_model=ReportResponse)
async def get_report(job_id: str):
    """Get the final report for a completed research job.

    Prefers the in-memory graph state; falls back to SQLite for jobs whose
    MemorySaver state was lost on restart.
    """
    thread = {"configurable": {"thread_id": job_id}}
    state = await graph.aget_state(thread)
    report: str | None = None
    if state.values:
        report = state.values.get("final_report")

    persisted = db.get_job(job_id)
    if not report and persisted:
        report = persisted.get("final_report")

    if not state.values and not persisted:
        raise HTTPException(status_code=404, detail="Job not found")

    status = "completed" if report else "in_progress"

    # Tokens: live tracker first, persisted second
    totals = get_token_totals(job_id)
    if totals["total"] == 0 and persisted and persisted.get("tokens"):
        totals = persisted["tokens"]

    return ReportResponse(
        job_id=job_id,
        status=status,
        report=report,
        tokens=TokenUsage(**totals),
    )


class HistoryItem(BaseModel):
    job_id: str
    company: str
    seed_url: str | None
    status: str
    kind: str
    created_at: str
    updated_at: str


class HistoryResponse(BaseModel):
    items: list[HistoryItem]


async def _run_research_to_completion(
    company: str, seed_url: str | None, job_id: str
) -> tuple[str, str, dict]:
    """Run a single research pipeline end-to-end (auto-approving the plan).

    Returns (company, final_report, token_totals). Used inside /research/compare
    so we can run both sides concurrently.
    """
    tracker = TokenTracker(job_id)
    thread = {
        "configurable": {"thread_id": job_id},
        "callbacks": [tracker],
    }

    # Phase 1: run until the interrupt at scraper_dispatch
    try:
        await graph.ainvoke(
            {"company": company, "seed_url": seed_url},
            config=thread,
        )
    except Exception as e:
        logger.debug(f"[compare:{company}] paused at checkpoint: {e}")

    state = await graph.aget_state(thread)
    plan = state.values.get("plan", [])
    db.insert_job(
        job_id=job_id, company=company, seed_url=seed_url, plan=plan, kind="single"
    )

    # Phase 2: auto-approve and drive to completion
    await graph.aupdate_state(thread, {"plan_approved": True})
    db.update_status(job_id, "running")

    # ainvoke(None) drives the graph forward from the checkpoint to END
    final_state = await graph.ainvoke(None, config=thread)
    final_report = (final_state or {}).get("final_report", "")

    totals = get_token_totals(job_id)
    db.save_completion(job_id=job_id, final_report=final_report, tokens=totals)
    return company, final_report, totals


async def _run_comparison_job(
    compare_job_id: str,
    company_a: str,
    seed_url_a: str | None,
    company_b: str,
    seed_url_b: str | None,
) -> None:
    """Background task: run both research pipelines, then comparator."""
    job_a = f"{compare_job_id}_a"
    job_b = f"{compare_job_id}_b"

    try:
        results = await asyncio.gather(
            _run_research_to_completion(company_a, seed_url_a, job_a),
            _run_research_to_completion(company_b, seed_url_b, job_b),
            return_exceptions=True,
        )

        report_a, report_b = "", ""
        totals_a: dict = {"input": 0, "output": 0, "total": 0, "calls": 0}
        totals_b: dict = {"input": 0, "output": 0, "total": 0, "calls": 0}

        for res in results:
            if isinstance(res, Exception):
                logger.error(f"[compare:{compare_job_id}] subjob failed: {res}")
                continue
            name, rep, tot = res
            if name == company_a:
                report_a, totals_a = rep, tot
            else:
                report_b, totals_b = rep, tot

        # Synthesize comparison (also tracked under the compare_job_id)
        compare_tracker = TokenTracker(compare_job_id)
        comparison = await run_comparator(
            company_a=company_a,
            company_b=company_b,
            report_a=report_a,
            report_b=report_b,
            callbacks=[compare_tracker],
        )

        comparator_totals = get_token_totals(compare_job_id)
        combined = {
            "input": totals_a["input"] + totals_b["input"] + comparator_totals["input"],
            "output": totals_a["output"] + totals_b["output"] + comparator_totals["output"],
            "total": totals_a["total"] + totals_b["total"] + comparator_totals["total"],
            "calls": totals_a["calls"] + totals_b["calls"] + comparator_totals["calls"],
        }

        db.save_completion(
            job_id=compare_job_id, final_report=comparison, tokens=combined
        )
    except Exception as e:
        logger.exception(f"[compare:{compare_job_id}] job failed: {e}")
        db.update_status(compare_job_id, "error")


class CompareRequest(BaseModel):
    company_a: str
    company_b: str
    website_url_a: str | None = None
    website_url_b: str | None = None


class CompareStartResponse(BaseModel):
    compare_job_id: str
    status: str


@router.post("/research/compare", response_model=CompareStartResponse)
async def start_comparison(req: CompareRequest):
    """Kick off a side-by-side comparison of two companies (background)."""
    _check_rate_limit()

    company_a = req.company_a.strip()
    company_b = req.company_b.strip()
    if not company_a or not company_b:
        raise HTTPException(status_code=400, detail="Both companies are required")

    def _normalize(url: str | None) -> str | None:
        u = (url or "").strip() or None
        if u and not u.startswith(("http://", "https://")):
            u = f"https://{u}"
        return u

    seed_a = _normalize(req.website_url_a)
    seed_b = _normalize(req.website_url_b)

    compare_job_id = str(uuid.uuid4())
    db.insert_job(
        job_id=compare_job_id,
        company=f"{company_a} vs {company_b}",
        seed_url=None,
        plan=[],
        kind="compare",
        meta={
            "company_a": company_a,
            "company_b": company_b,
            "seed_url_a": seed_a,
            "seed_url_b": seed_b,
        },
    )
    db.update_status(compare_job_id, "running")

    logger.info(
        f"Starting comparison {compare_job_id}: {company_a} vs {company_b}"
    )

    # Fire and forget — the frontend polls /research/{id}/report
    asyncio.create_task(
        _run_comparison_job(
            compare_job_id=compare_job_id,
            company_a=company_a,
            seed_url_a=seed_a,
            company_b=company_b,
            seed_url_b=seed_b,
        )
    )

    return CompareStartResponse(compare_job_id=compare_job_id, status="running")


@router.get("/research/history", response_model=HistoryResponse)
async def list_history(limit: int = 50):
    """Return recent research jobs (newest first)."""
    rows = db.list_jobs(limit=limit)
    items = [
        HistoryItem(
            job_id=r["id"],
            company=r["company"],
            seed_url=r.get("seed_url"),
            status=r["status"],
            kind=r.get("kind", "single"),
            created_at=r["created_at"],
            updated_at=r["updated_at"],
        )
        for r in rows
    ]
    return HistoryResponse(items=items)
