# FAME Orchestrator - Production Orchestration Layer

## Overview

The orchestrator layer provides a production-ready wrapper around FAME's core modules, adding:
- Dynamic plugin loading
- Event-based communication
- Sandboxed code execution (Docker-based)
- Evolution cycles
- Safety controls and audit logging
- REST API interface

## Quick Start

### 1. Install Dependencies

```bash
pip install fastapi uvicorn docker
```

### 2. Run API Server

```bash
python orchestrator/api_server.py
```

Server starts on `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 3. Test Query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"text": "Write a Python function to reverse a string", "intent": "generate_code"}'
```

## Architecture

```
orchestrator/
├── plugin_loader.py    # Auto-discovers and loads core/ modules
├── event_bus.py        # Pub/sub event system
├── brain.py            # Master orchestrator (routes queries)
├── docker_manager.py   # Sandbox execution (requires Docker)
├── sandbox_runner.py  # Fallback runner (dev only, NOT secure)
├── evolution_runner.py # Evolution cycle coordinator
├── voice_adapter.py    # Voice I/O integration
└── api_server.py       # FastAPI REST endpoint
```

## Plugin Interface

Core modules should implement:

```python
# Module-level functions (or class methods)
def init(manager):
    """Called when plugin is loaded"""
    global MANAGER
    MANAGER = manager

def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle query from orchestrator"""
    text = request.get('text', '')
    intent = request.get('intent', '')
    
    # Process query...
    
    return {
        "response": "...",
        "metadata": {...}
    }
```

## Safety Features

### Default Settings (Conservative)
- Network access: **DISABLED** by default
- Sandbox execution: **REQUIRED** for all generated code
- Admin keys: **REQUIRED** for dangerous operations
- Audit logging: **ENABLED** for all queries

### Enable Network Access
```python
brain.allow_network = True  # Only in trusted environments
```

### Add Admin Keys
```python
brain.admin_api_keys.add('your-admin-key-here')
```

## Example Queries

### Code Generation
```json
{
  "text": "Write a Python function to reverse a string",
  "intent": "generate_code",
  "user": "test_user"
}
```

Expected response includes:
- Generated code
- Sandbox test report (exit code, stdout, stderr)

### Market Analysis
```json
{
  "text": "What is BTC price today?",
  "intent": "market_analysis",
  "user": "test_user"
}
```

Routes to: `advanced_investor_ai`, `web_scraper`

### Evolution Cycle (Admin Only)
```bash
curl -X POST http://localhost:8000/evolution/run \
  -H "X-API-Key: your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"population_size": 5, "task": "optimize code generation"}'
```

## Docker Sandbox

### Requirements
- Docker daemon running
- `python:3.11-slim` image (pulled automatically if needed)

### Configuration
```python
# In brain.py or api_server.py
brain.docker_manager.run_code_in_container(
    code_str="...",
    timeout_seconds=30,
    memory_limit='512m',
    cpu_quota=50000,  # 0.5 cores
    allow_network=False
)
```

## Evolution Runner

```python
from orchestrator.brain import Brain
from orchestrator.evolution_runner import EvolutionRunner

brain = Brain()
runner = EvolutionRunner(brain)

# Run evolution cycle
result = await runner.run_generation(
    population_size=5,
    task="optimize string reversal"
)
```

## Audit Logging

All queries and responses are logged:

```python
# Get audit log
audit = brain.audit_log[-100:]  # Last 100 entries

# Via API
GET /audit?limit=100
```

## Production Checklist

Before deploying:

- [ ] Set up persistent audit log storage (DB/S3)
- [ ] Configure admin API keys
- [ ] Enable Docker sandbox (disable local runner)
- [ ] Add input sanitization
- [ ] Set up rate limiting
- [ ] Configure CORS properly
- [ ] Add authentication middleware
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Enable PII filtering in logs
- [ ] Configure human approval for promotions

## Testing

```bash
# Run integration tests
python tests/test_orchestrator.py

# Test plugin loading
python -c "from orchestrator.plugin_loader import load_plugins; print(load_plugins())"
```

## Troubleshooting

### Docker Not Available
- Install Docker Desktop
- Or use local sandbox runner (dev only): `brain.sandbox_runner = run_code_locally`

### Plugin Not Loading
- Check `core/` folder exists
- Verify module has no syntax errors
- Check `orchestrator/plugin_loader.py` logs

### Query Routing Issues
- Check `brain._simple_route()` keyword matching
- Add custom routing in `brain.handle_query()`
- Use `consciousness_engine` for intelligent routing

## Next Steps

1. Add wrapper functions to remaining core modules
2. Implement persistent audit logging
3. Add telemetry dashboard
4. Set up CI/CD pipeline
5. Enable canary deployments
6. Add RLHF feedback loop

## License

See main FAME license.

