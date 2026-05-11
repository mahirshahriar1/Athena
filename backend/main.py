"""FastAPI application entrypoint for Athena."""

import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.api.routes import router
from backend.api.ws import research_websocket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Athena - Competitive Intelligence Platform",
    description="Autonomous AI-powered competitive research",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST routes
app.include_router(router)


# WebSocket route
@app.websocket("/api/ws/research/{job_id}")
async def ws_research(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for streaming research progress."""
    await research_websocket(websocket, job_id)


# Health check
@app.get("/health")
async def health():
    return {"status": "ok", "service": "athena"}


@app.on_event("startup")
async def startup():
    logger.info("Athena backend starting up")
    logger.info(f"CORS origins: {settings.CORS_ORIGINS}")
    logger.info(f"ChromaDB dir: {settings.CHROMA_PERSIST_DIR}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
