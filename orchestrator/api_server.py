# orchestrator/api_server.py

"""
Lightweight FastAPI server for FAME orchestration layer
"""

try:
    from fastapi import FastAPI, HTTPException, Request, Header
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("⚠️ FastAPI not installed. Install with: pip install fastapi uvicorn")
    print("   API server will not be available.")

import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from orchestrator.brain import Brain

if FASTAPI_AVAILABLE:
    app = FastAPI(title="FAME Orchestrator API", version="1.0.0")
    
    # Enable CORS for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize brain
    brain = Brain()
    
    # Try to initialize Docker manager for sandboxing
    try:
        from orchestrator.docker_manager import DockerManager
        brain.docker_manager = DockerManager()
        print("[API] ✅ Docker sandbox available")
    except Exception as e:
        print(f"[API] ⚠️ Docker sandbox unavailable: {e}")
        # Fallback to local runner (NOT SECURE for production)
        from orchestrator.sandbox_runner import run_code_locally
        brain.sandbox_runner = run_code_locally
        print("[API] ⚠️ Using local sandbox runner (development only)")
    
    @app.get("/")
    async def root():
        return {
            "name": "FAME Orchestrator",
            "version": "1.0.0",
            "status": "online",
            "plugins_loaded": len(brain.plugins),
            "plugin_names": list(brain.plugins.keys())
        }
    
    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "plugins": len(brain.plugins),
            "audit_log_size": len(brain.audit_log)
        }
    
    @app.post("/query")
    async def query(
        payload: dict,
        x_api_key: Optional[str] = Header(None, alias="X-API-Key")
    ):
        """
        Handle query from client.
        
        Example payload:
        {
          "text": "Write a Python function to reverse a string",
          "intent": "generate_code",
          "user": "test_user"
        }
        """
        # Simple auth check (expand for production)
        if x_api_key and x_api_key not in brain.admin_api_keys:
            # Still allow but log
            brain.audit_log.append({
                "event": "api.query_with_unknown_key",
                "key_prefix": x_api_key[:8] if x_api_key else None
            })
        
        try:
            resp = await brain.handle_query(payload)
            return resp
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/audit")
    async def get_audit(limit: int = 100):
        """Get audit log (admin only in production)"""
        return {
            "audit_log": brain.audit_log[-limit:],
            "total_entries": len(brain.audit_log)
        }
    
    @app.get("/plugins")
    async def list_plugins():
        """List all loaded plugins"""
        plugin_info = {}
        for name, plugin in brain.plugins.items():
            info = {"name": name}
            if hasattr(plugin, 'info'):
                try:
                    info.update(plugin.info() if callable(plugin.info) else plugin.info)
                except:
                    pass
            plugin_info[name] = info
        return {"plugins": plugin_info}
    
    @app.post("/evolution/run")
    async def run_evolution(
        payload: dict,
        x_api_key: Optional[str] = Header(None, alias="X-API-Key")
    ):
        """Run evolution cycle (admin only)"""
        # Check admin key
        if not x_api_key or x_api_key not in brain.admin_api_keys:
            raise HTTPException(status_code=403, detail="Admin key required")
        
        from orchestrator.evolution_runner import EvolutionRunner
        runner = EvolutionRunner(brain)
        
        population_size = payload.get("population_size", 3)
        task = payload.get("task", None)
        
        try:
            result = await runner.run_generation(population_size, task)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    if __name__ == "__main__":
        print("=" * 60)
        print("FAME Orchestrator API Server")
        print("=" * 60)
        print(f"✅ Loaded {len(brain.plugins)} plugins")
        print("🌐 Starting server on http://0.0.0.0:8000")
        print("📚 API docs available at http://localhost:8000/docs")
        print("=" * 60)
        
        uvicorn.run(app, host="0.0.0.0", port=8000)
else:
    # Fallback if FastAPI not available
    print("API server requires FastAPI. Install with: pip install fastapi uvicorn")
    print("You can still use the Brain class directly:")
    print("  from orchestrator.brain import Brain")
    print("  brain = Brain()")
    print("  response = await brain.handle_query({'text': 'your query'})")

