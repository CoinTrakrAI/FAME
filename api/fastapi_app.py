#!/usr/bin/env python3
"""
FAME AGI - Production FastAPI Service
Enhanced microservice with planning, reflection, and autonomous operation
"""

import uvicorn
import asyncio
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import yaml
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agi_core import AGICore
from utils.logger import AGILogger
from utils.monitoring import SystemMonitor

# Setup logging
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
        "models": {"primary_llm": "gpt-4o-mini", "embedding_model": "text-embedding-3-large"},
        "spiders": {"enabled": True, "count": 10},
        "execution": {"dual_core": True, "local_model": "llama2"},
        "api": {"host": "0.0.0.0", "port": 8080, "cors_enabled": True}
    }

# Initialize components
agi_logger = AGILogger(cfg)
monitor = SystemMonitor()
agi = None  # Will be initialized on startup

app = FastAPI(
    title="FAME AGI Service",
    description="Autonomous General Intelligence Core - Production Service",
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


class PlanRequest(BaseModel):
    goal: str
    parameters: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """Initialize AGI core on startup"""
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
    """Graceful shutdown"""
    global agi
    if agi:
        try:
            await agi.shutdown()
            logger.info("AGI Core shut down gracefully")
        except Exception as e:
            logger.error(f"Shutdown error: {e}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
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


@app.get("/metrics")
async def get_metrics():
    """System metrics endpoint"""
    global agi
    if not agi:
        raise HTTPException(status_code=503, detail="AGI Core not initialized")
    
    metrics = {
        "system_metrics": agi.metrics,
        "performance_metrics": monitor.get_performance_metrics(),
        "persona_profile": agi.persona.profile if agi.persona else {}
    }
    
    # Add autonomous engine metrics if available
    if hasattr(agi.autonomous_engine, 'metrics'):
        metrics["autonomous_engine_metrics"] = agi.autonomous_engine.metrics
    
    # Add memory stats if available
    if hasattr(agi.autonomous_engine, 'memory'):
        try:
            metrics["memory_stats"] = agi.autonomous_engine.memory.stats()
        except Exception:
            pass
    
    return metrics


@app.post("/ask")
async def ask_agi(request: AskRequest):
    """
    Main AGI query endpoint with full planning and reflection pipeline
    """
    global agi
    if not agi:
        raise HTTPException(status_code=503, detail="AGI Core not initialized")
    
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


@app.post("/plan")
async def create_plan(request: PlanRequest):
    """Create a new plan for a goal"""
    global agi
    if not agi or not agi.planner:
        raise HTTPException(status_code=503, detail="Planning not available")
    
    try:
        plan = agi.planner.decompose(request.goal, request.parameters)
        agi.active_plans[plan.id] = plan
        
        return {
            "success": True,
            "plan_id": plan.id,
            "goal": plan.goal,
            "tasks": plan.tasks,
            "created_at": plan.created_at
        }
    except Exception as e:
        logger.error(f"Planning failed: {e}")
        raise HTTPException(status_code=500, detail=f"Planning failed: {str(e)}")


@app.get("/plan/{plan_id}")
async def get_plan(plan_id: str):
    """Get plan status and results"""
    global agi
    if not agi:
        raise HTTPException(status_code=503, detail="AGI Core not initialized")
    
    plan = agi.active_plans.get(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    return {
        "plan": plan.to_dict() if hasattr(plan, 'to_dict') else {"id": plan.id, "goal": getattr(plan, 'goal', '')},
        "status": "active"
    }


@app.post("/feedback")
async def submit_feedback(feedback: Dict[str, Any]):
    """Submit feedback for AGI learning"""
    global agi
    if not agi:
        raise HTTPException(status_code=503, detail="AGI Core not initialized")
    
    try:
        # Update persona if feedback includes preferences
        if agi.persona and ("tone_preference" in feedback or "verbosity" in feedback):
            try:
                agi.persona.update_from_feedback(feedback)
            except Exception:
                pass
        
        # Record reward for RL if available
        if agi.rl and "reward" in feedback:
            try:
                agi.rl.record(
                    query=feedback.get("query", ""),
                    response_id=feedback.get("response_id", ""),
                    reward=feedback["reward"],
                    metadata=feedback
                )
            except Exception:
                pass
        
        return {"success": True, "message": "Feedback recorded"}
    except Exception as e:
        logger.error(f"Feedback processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Feedback processing failed: {str(e)}")


@app.get("/persona")
async def get_persona():
    """Get current persona profile"""
    global agi
    if not agi or not agi.persona:
        return {"profile": {"tone": "professional", "verbosity": "medium"}}
    
    return agi.persona.profile


@app.post("/persona")
async def update_persona(updates: Dict[str, Any]):
    """Update persona profile"""
    global agi
    if not agi or not agi.persona:
        raise HTTPException(status_code=503, detail="Persona not available")
    
    try:
        agi.persona.update_from_feedback(updates)
        return {"success": True, "profile": agi.persona.profile}
    except Exception as e:
        logger.error(f"Persona update failed: {e}")
        raise HTTPException(status_code=500, detail=f"Persona update failed: {str(e)}")


# Background tasks for autonomous operation
async def autonomous_background_loop():
    """Background loop for autonomous AGI operations"""
    global agi
    while True:
        try:
            if agi:
                await agi.run_autonomous_cycle()
            await asyncio.sleep(60)  # Run every minute
        except Exception as e:
            logger.error(f"Background loop error: {e}")
            await asyncio.sleep(10)


@app.on_event("startup")
async def start_background_tasks():
    """Start background autonomous processing"""
    asyncio.create_task(autonomous_background_loop())


if __name__ == "__main__":
    api_config = cfg.get("api", {})
    uvicorn.run(
        app,
        host=api_config.get("host", "0.0.0.0"),
        port=api_config.get("port", 8080),
        log_level="info",
        access_log=True
    )

