"""Per-job token usage tracking via a LangChain callback handler.

Aggregates `usage_metadata` from every LLM call made during a graph run,
keyed by job_id. Read totals back with `get_token_totals(job_id)`.
"""

import logging
from typing import Any
from langchain_core.callbacks import AsyncCallbackHandler

logger = logging.getLogger(__name__)

# {job_id: {"input": int, "output": int, "total": int, "calls": int}}
_token_totals: dict[str, dict[str, int]] = {}


def _empty() -> dict[str, int]:
    return {"input": 0, "output": 0, "total": 0, "calls": 0}


class TokenTracker(AsyncCallbackHandler):
    """LangChain async callback that accumulates token usage per job_id."""

    def __init__(self, job_id: str):
        super().__init__()
        self.job_id = job_id
        _token_totals.setdefault(job_id, _empty())

    async def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        try:
            bucket = _token_totals.setdefault(self.job_id, _empty())
            counted = False

            # Path 1: usage_metadata on each generation's message (modern wrappers)
            for gen_list in getattr(response, "generations", []) or []:
                for gen in gen_list:
                    msg = getattr(gen, "message", None)
                    usage = getattr(msg, "usage_metadata", None) if msg else None
                    if usage:
                        bucket["input"] += int(usage.get("input_tokens", 0) or 0)
                        bucket["output"] += int(usage.get("output_tokens", 0) or 0)
                        bucket["total"] += int(usage.get("total_tokens", 0) or 0)
                        bucket["calls"] += 1
                        counted = True

            # Path 2: llm_output.token_usage (older OpenAI-style)
            if not counted:
                llm_output = getattr(response, "llm_output", None) or {}
                usage = llm_output.get("token_usage") or llm_output.get("usage") or {}
                if usage:
                    pt = int(usage.get("prompt_tokens", 0) or 0)
                    ct = int(usage.get("completion_tokens", 0) or 0)
                    tt = int(usage.get("total_tokens", pt + ct) or 0)
                    bucket["input"] += pt
                    bucket["output"] += ct
                    bucket["total"] += tt
                    bucket["calls"] += 1
        except Exception as e:
            logger.debug(f"TokenTracker failed for job {self.job_id}: {e}")


def get_token_totals(job_id: str) -> dict[str, int]:
    """Return aggregated token counts for a job (zeros if unseen)."""
    return dict(_token_totals.get(job_id, _empty()))


def reset_token_totals(job_id: str) -> None:
    _token_totals.pop(job_id, None)
