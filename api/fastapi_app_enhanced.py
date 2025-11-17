#!/usr/bin/env python3
"""
FAME AGI - Enhanced Production Microservice
FastAPI with WebSocket, streaming responses, and advanced endpoints
"""

import uvicorn
import asyncio
import logging
import json
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List, AsyncGenerator
import yaml
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agi_core import AGICore
from utils.logger import AGILogger
from utils.monitoring import SystemMonitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
CFG_PATH = Path(__file__).parent.parent / "config.yaml"
if CFG_PATH.exists():
    with open(CFG_PATH, 'r') as f:
        cfg = yaml.safe_load(f)
else:
    cfg = {
        "system": {"name": "FAME AGI", "version": "6.1", "mode": "autonomous"},
        "api": {"host": "0.0.0.0", "port": 8080, "cors_enabled": True}
    }

# Initialize components
agi_logger = AGILogger(cfg)
monitor = SystemMonitor()
agi = None
active_websockets: List[WebSocket] = []

app = FastAPI(
    title="FAME AGI Service",
    description="Autonomous General Intelligence Core - Enhanced Production Service",
    version=cfg.get("system", {}).get("version", "6.1")
)

# CORS middleware
if cfg.get("api", {}).get("cors_enabled", True):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


class AskRequest(BaseModel):
    prompt: str
    context: Optional[List[Dict[str, str]]] = None
    stream: bool = False


@app.on_event("startup")
async def startup_event():
    global agi
    try:
        logger.info("FAME AGI Service starting up...")
        agi = AGICore(cfg)
        logger.info("AGI Core initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AGI Core: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    global agi
    if agi:
        try:
            await agi.shutdown()
            logger.info("AGI Core shut down gracefully")
        except Exception as e:
            logger.error(f"Shutdown error: {e}")


@app.get("/health")
async def health_check():
    global agi
    health_status = await monitor.check_health()
    
    components = {
        "memory": agi.memory is not None if agi else False,
        "planner": agi.planner is not None if agi else False,
        "task_manager": agi.task_manager is not None if agi else False,
        "reflector": agi.reflector is not None if agi else False,
        "autonomous_engine": agi.autonomous_engine is not None if agi else False
    }
    
    return {
        "status": "healthy" if agi else "initializing",
        "system": cfg.get("system", {}).get("name", "FAME AGI"),
        "version": cfg.get("system", {}).get("version", "6.1"),
        "components": components,
        "system_health": health_status
    }


@app.post("/ask")
async def ask_agi(request: AskRequest):
    """Main AGI query endpoint with optional streaming"""
    global agi
    if not agi:
        raise HTTPException(status_code=503, detail="AGI Core not initialized")
    
    if request.stream:
        return StreamingResponse(
            stream_response(request.prompt, request.context),
            media_type="text/event-stream"
        )
    
    try:
        result = await agi.run(request.prompt, request.context)
        return {
            "success": True,
            "response": result["response"],
            "confidence": result["confidence"],
            "plan_id": result.get("plan_id"),
            "audit_score": result.get("audit_report", {}).get("score", result["confidence"]),
            "sources_used": result.get("sources", []),
            "breakdown": result.get("breakdown", []),
            "metrics": result.get("metrics", {})
        }
    except Exception as e:
        logger.error(f"AGI query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AGI processing error: {str(e)}")


async def stream_response(prompt: str, context: Optional[List[Dict[str, str]]]) -> AsyncGenerator[str, None]:
    """Stream response tokens as they're generated"""
    global agi
    try:
        # Simulate streaming (in production, would stream from LLM)
        result = await agi.run(prompt, context)
        response = result["response"]
        
        # Stream response word by word
        words = response.split()
        for i, word in enumerate(words):
            chunk = {
                "token": word,
                "index": i,
                "done": i == len(words) - 1
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.05)  # Simulate generation delay
        
        # Final metadata
        final_chunk = {
            "done": True,
            "confidence": result.get("confidence", 0.0),
            "sources": result.get("sources", [])
        }
        yield f"data: {json.dumps(final_chunk)}\n\n"
    except Exception as e:
        error_chunk = {"error": str(e), "done": True}
        yield f"data: {json.dumps(error_chunk)}\n\n"


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    active_websockets.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "query":
                prompt = message.get("prompt", "")
                context = message.get("context", [])
                
                # Process query
                result = await agi.run(prompt, context)
                
                # Send response
                await websocket.send_json({
                    "type": "response",
                    "response": result["response"],
                    "confidence": result["confidence"],
                    "sources": result.get("sources", [])
                })
            
            elif message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            
    except WebSocketDisconnect:
        active_websockets.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in active_websockets:
            active_websockets.remove(websocket)


@app.post("/memory/wipe")
async def wipe_memory(confirm: bool = False):
    """Wipe memory (requires confirmation)"""
    if not confirm:
        raise HTTPException(status_code=400, detail="Confirmation required")
    
    global agi
    if not agi or not hasattr(agi.autonomous_engine, 'memory'):
        raise HTTPException(status_code=503, detail="Memory not available")
    
    try:
        # Clear memory
        agi.autonomous_engine.memory._mem = {
            "conversations": [],
            "knowledge": {},
            "patterns": {},
            "source_stats": {},
            "meta": {}
        }
        agi.autonomous_engine.memory.save(force=True)
        
        return {"status": "success", "message": "Memory wiped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Memory wipe failed: {str(e)}")


@app.post("/memory/rebuild")
async def rebuild_vector_store(background_tasks: BackgroundTasks):
    """Rebuild vector store index"""
    global agi
    if not agi or not hasattr(agi.autonomous_engine, 'embed'):
        raise HTTPException(status_code=503, detail="Vector store not available")
    
    def rebuild_task():
        # Rebuild embedding index
        if hasattr(agi.autonomous_engine.embed, 'index'):
            # Clear and rebuild
            agi.autonomous_engine.embed.index = None
            agi.autonomous_engine.embed.id_to_meta = {}
            agi.autonomous_engine.embed.next_id = 0
    
    background_tasks.add_task(rebuild_task)
    
    return {"status": "started", "message": "Vector store rebuild initiated"}


@app.get("/metrics")
async def get_metrics():
    """System metrics endpoint"""
    global agi
    if not agi:
        raise HTTPException(status_code=503, detail="AGI Core not initialized")
    
    metrics = {
        "system_metrics": agi.metrics,
        "performance_metrics": monitor.get_performance_metrics(),
        "persona_profile": agi.persona.profile if agi.persona else {},
        "websocket_connections": len(active_websockets)
    }
    
    if hasattr(agi.autonomous_engine, 'metrics'):
        metrics["autonomous_engine_metrics"] = agi.autonomous_engine.metrics
    
    if hasattr(agi.autonomous_engine, 'memory'):
        try:
            metrics["memory_stats"] = agi.autonomous_engine.memory.stats()
        except Exception:
            pass
    
    return metrics


if __name__ == "__main__":
    api_config = cfg.get("api", {})
    uvicorn.run(
        app,
        host=api_config.get("host", "0.0.0.0"),
        port=api_config.get("port", 8080),
        log_level="info",
        access_log=True
    )

