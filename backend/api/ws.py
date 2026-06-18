"""WebSocket handler for streaming research progress."""

import logging
import json
from fastapi import WebSocket, WebSocketDisconnect
from backend.graph.builder import graph
from backend.core.tokens import TokenTracker, get_token_totals
from backend.core import db

logger = logging.getLogger(__name__)


async def research_websocket(websocket: WebSocket, job_id: str):
    """Stream graph execution events over WebSocket.

    Events sent to client:
    - {"type": "node_start", "node": "planner", "timestamp": ...}
    - {"type": "token", "node": "writer", "content": "..."}
    - {"type": "node_done", "node": "planner", "output": {...}}
    - {"type": "error", "message": "..."}
    - {"type": "complete", "job_id": "..."}
    """
    await websocket.accept()
    tracker = TokenTracker(job_id)
    thread = {
        "configurable": {"thread_id": job_id},
        "callbacks": [tracker],
    }

    logger.info(f"WebSocket connected for job {job_id}")

    try:
        # Stream events from graph execution
        async for event in graph.astream_events(
            None,
            config=thread,
            version="v2",
        ):
            event_type = event.get("event", "")

            if event_type == "on_chain_start":
                node_name = event.get("name", "")
                if node_name and not node_name.startswith("_"):
                    await websocket.send_json({
                        "type": "node_start",
                        "node": node_name,
                        "timestamp": event.get("metadata", {}).get("created_at"),
                    })

            elif event_type == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    node = event.get("metadata", {}).get("langgraph_node", "")
                    await websocket.send_json({
                        "type": "token",
                        "node": node,
                        "content": chunk.content,
                    })

            elif event_type == "on_chain_end":
                node_name = event.get("name", "")
                if node_name and not node_name.startswith("_"):
                    output = event.get("data", {}).get("output")
                    # Serialize output safely
                    safe_output = None
                    if isinstance(output, dict):
                        try:
                            safe_output = json.loads(json.dumps(output, default=str))
                        except (TypeError, ValueError):
                            safe_output = {"status": "completed"}

                    await websocket.send_json({
                        "type": "node_done",
                        "node": node_name,
                        "output": safe_output,
                    })

        # Persist final report + token totals to SQLite so /history and a
        # post-restart /report fallback work.
        try:
            state = await graph.aget_state({"configurable": {"thread_id": job_id}})
            final_report = state.values.get("final_report") if state.values else None
            if final_report:
                db.save_completion(
                    job_id=job_id,
                    final_report=final_report,
                    tokens=get_token_totals(job_id),
                )
        except Exception as save_err:
            logger.warning(f"Could not persist completion for {job_id}: {save_err}")

        # Signal completion (with token totals)
        await websocket.send_json({
            "type": "complete",
            "job_id": job_id,
            "tokens": get_token_totals(job_id),
        })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
            })
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
