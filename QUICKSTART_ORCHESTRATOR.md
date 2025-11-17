# 🚀 FAME Orchestrator - Quick Start Guide

## Installation (2 minutes)

### 1. Install Python Dependencies

```bash
pip install fastapi uvicorn docker
```

**Optional (for development):**
```bash
pip install pytest flake8
```

### 2. Verify Docker (for sandbox)

```bash
docker --version
docker pull python:3.11-slim
```

If Docker is not available, the orchestrator will fall back to a local runner (development only, NOT secure for production).

## Run API Server

```bash
cd C:\Users\cavek\Downloads\FAME_Desktop
python orchestrator/api_server.py
```

You should see:
```
============================================================
FAME Orchestrator API Server
============================================================
✅ Loaded X plugins
🌐 Starting server on http://0.0.0.0:8000
📚 API docs available at http://localhost:8000/docs
============================================================
```

## Test It Works

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected:
```json
{
  "status": "healthy",
  "plugins": 15,
  "audit_log_size": 0
}
```

### 2. List Plugins

```bash
curl http://localhost:8000/plugins
```

### 3. Send a Query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"Write a Python function to reverse a string\", \"intent\": \"generate_code\"}"
```

Expected response includes:
- Generated Python code
- Sandbox test report (if Docker available)

## Run Tests

```bash
python tests/test_orchestrator.py
```

## Example Queries

See `tests/example_queries.json` for more examples.

### Code Generation
```json
{
  "text": "Write a function to reverse a string",
  "intent": "generate_code"
}
```

### Market Analysis
```json
{
  "text": "What is BTC price today?",
  "intent": "market_analysis"
}
```

### Architecture Design
```json
{
  "text": "Design a reverse proxy architecture",
  "intent": "architecture_design"
}
```

## Using Brain Directly (Python)

```python
import asyncio
from orchestrator.brain import Brain

# Initialize
brain = Brain()

# Handle query
async def main():
    query = {
        'text': 'reverse a string',
        'intent': 'generate_code'
    }
    
    response = await brain.handle_query(query)
    print(response)

asyncio.run(main())
```

## Development Workflow

1. **Modify core modules** in `core/`
2. **Add wrapper functions** if needed:
   ```python
   def init(manager):
       global MANAGER
       MANAGER = manager
   
   def handle(request):
       # Process query
       return {"response": "..."}
   ```
3. **Restart API server** - plugins auto-reload on restart
4. **Test with curl or tests/**

## Troubleshooting

### "Docker daemon not running"
- Start Docker Desktop (Windows/Mac)
- Or use local sandbox runner: `brain.sandbox_runner = run_code_locally`

### "Module not found"
- Check `core/` folder exists
- Verify Python path: `python -c "import sys; print(sys.path)"`

### "Plugin not responding"
- Check plugin has `init()` and `handle()` functions
- Review `orchestrator/plugin_loader.py` logs

### "Query not routing correctly"
- Check keywords in `brain._simple_route()`
- Use `consciousness_engine` for intelligent routing

## Next Steps

1. ✅ Basic setup complete
2. 🔜 Add wrapper functions to more core modules
3. 🔜 Set up persistent audit logging
4. 🔜 Configure admin API keys
5. 🔜 Add telemetry dashboard
6. 🔜 Enable evolution cycles

## Files Created

```
orchestrator/
├── __init__.py
├── plugin_loader.py      # Auto-discovers core/ modules
├── event_bus.py          # Event system
├── brain.py              # Master orchestrator
├── docker_manager.py     # Sandbox execution
├── sandbox_runner.py     # Dev fallback
├── evolution_runner.py    # Evolution cycles
├── voice_adapter.py      # Voice I/O
├── api_server.py         # REST API
└── README_ORCHESTRATOR.md

tests/
├── test_orchestrator.py  # Integration tests
└── example_queries.json  # Query examples
```

## Production Checklist

Before deploying to production:

- [ ] Set `brain.allow_network = False` (default)
- [ ] Configure admin API keys
- [ ] Enable Docker sandbox (disable local runner)
- [ ] Set up persistent audit log (DB/S3)
- [ ] Add input sanitization
- [ ] Configure CORS properly
- [ ] Add rate limiting
- [ ] Set up monitoring
- [ ] Enable PII filtering
- [ ] Configure human approval for promotions

---

**Ready to build!** 🎉

For detailed documentation, see `orchestrator/README_ORCHESTRATOR.md`

