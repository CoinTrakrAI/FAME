"""
Minimal FastAPI server exposing FAME query and health endpoints.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fame_unified import get_fame

logger = logging.getLogger(__name__)

app = FastAPI(title="FAME API", version="0.1.0", docs_url="/docs", redoc_url="/redoc")

# Enable CORS - Allow all origins for now (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins - change to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


class QueryRequest(BaseModel):
    text: str
    session_id: Optional[str] = None
    source: Optional[str] = None
    metadata: Dict[str, Any] | None = None


@app.on_event("startup")
async def startup_event() -> None:
    # Instantiate FAME and run an initial health check
    try:
        logger.info("Initializing FAME on startup...")
        fame = get_fame()
        logger.info("FAME initialized successfully")
        # Don't call health check on startup - let it be lazy
        # fame.health_monitor.check_system_health()
    except Exception as e:
        logger.error(f"FAME initialization failed on startup: {e}", exc_info=True)
        # Don't crash - let endpoints handle it


@app.get("/healthz", tags=["health"])
async def healthcheck() -> Dict[str, Any]:
    try:
        fame = get_fame()
        status = fame.health_monitor.check_system_health()
        return status
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "overall_status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }


@app.get("/readyz", tags=["health"])
async def readiness() -> Dict[str, Any]:
    try:
        fame = get_fame()
        status = fame.health_monitor.check_system_health()
        overall = status.get("overall_status", "unknown")
        if overall != "healthy":
            raise HTTPException(status_code=503, detail=status)
        return {"status": "ready", "timestamp": status.get("timestamp")}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail={"error": str(e)})


@app.post("/query", tags=["fame"])
async def process_query(request: QueryRequest) -> Dict[str, Any]:
    try:
        fame = get_fame()
        session_id = request.session_id or f"session_{int(time.time())}"
        payload = {
            "text": request.text,
            "session_id": session_id,
            "source": request.source or "api",
            "metadata": request.metadata or {},
        }
        response = await fame.process_query(payload)
        return response
    except Exception as e:
        logger.error(f"Query processing failed: {e}", exc_info=True)
        return {
            "response": f"Error processing query: {str(e)}",
            "confidence": 0.0,
            "error": str(e),
            "timestamp": time.time()
        }
