# FAME AGI - Production Deployment Guide

## 🚀 Complete Production AGI Stack

This guide covers deploying the **FAME AGI Core** - a production-ready autonomous general intelligence system with planning, reflection, and continuous learning.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   FAME AGI Core                          │
├─────────────────────────────────────────────────────────┤
│  🧠 AGI Core (Planning, Reflection, Task Management)     │
│  💾 Autonomous Response Engine (Vector Memory, LLMs)    │
│  🕷️  Web Spiders (Async Intelligence Gathering)        │
│  📊 System Monitoring & Health Checks                   │
│  📝 Enterprise Logging                                  │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone <your-repo>
cd FAME_Desktop

# Install dependencies
pip install -r requirements_production.txt

# Optional: Install additional AGI dependencies
pip install pyyaml psutil
```

### 2. Configuration

Create or edit `config.yaml`:

```yaml
system:
  name: "FAME AGI"
  version: "6.1"
  mode: "autonomous"

models:
  primary_llm: "gpt-4o-mini"
  embedding_model: "text-embedding-3-large"

api:
  host: "0.0.0.0"
  port: 8080
```

Set environment variables:

```bash
export OPENAI_API_KEY="your-key"
export GOOGLE_AI_KEY="your-key"
export SERPAPI_KEY="your-key"
```

### 3. Run as Service

**Option A: FastAPI Service (Recommended)**

```bash
python -m api.fastapi_app
# Or
python main.py service
```

**Option B: Continuous AGI Loop**

```bash
python main.py
```

**Option C: Docker Deployment**

```bash
docker-compose -f docker-compose.agi.yml up -d
```

## API Endpoints

### Health & Status

```bash
# Health check
curl http://localhost:8080/health

# Metrics
curl http://localhost:8080/metrics
```

### Query FAME AGI

```bash
curl -X POST http://localhost:8080/ask \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What are the current market trends in AI stocks?",
    "context": []
  }'
```

### Planning

```bash
# Create a plan
curl -X POST http://localhost:8080/plan \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Research renewable energy investment opportunities"
  }'

# Get plan status
curl http://localhost:8080/plan/{plan_id}
```

### Feedback & Learning

```bash
# Submit feedback
curl -X POST http://localhost:8080/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "query": "previous query",
    "response_id": "response_id",
    "reward": 0.8,
    "tone_preference": "professional"
  }'
```

### Persona Management

```bash
# Get persona
curl http://localhost:8080/persona

# Update persona
curl -X POST http://localhost:8080/persona \
  -H "Content-Type: application/json" \
  -d '{
    "tone": "friendly",
    "verbosity": "high"
  }'
```

## Docker Deployment

### Build and Run

```bash
# Build image
docker build -f Dockerfile.agi -t fame-agi:latest .

# Run container
docker run -d \
  -p 8080:8080 \
  -e OPENAI_API_KEY="your-key" \
  -e GOOGLE_AI_KEY="your-key" \
  -v $(pwd)/fame_data:/app/fame_data \
  -v $(pwd)/logs:/app/logs \
  --name fame-agi \
  fame-agi:latest

# Or use docker-compose
docker-compose -f docker-compose.agi.yml up -d
```

### With Monitoring (Prometheus + Grafana)

```bash
docker-compose -f docker-compose.agi.yml --profile monitoring up -d
```

Access:
- AGI Service: http://localhost:8080
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

## Features

### ✅ Core Capabilities

- **Autonomous Response Generation** - Production-ready engine with vector memory, web scraping, and dual-core LLM execution
- **Planning & Task Management** - Multi-step goal decomposition and execution
- **Self-Reflection** - Automatic quality verification and re-planning
- **Continuous Learning** - RL-based improvement from feedback
- **Persona Adaptation** - Adaptive tone and behavior based on interactions
- **System Monitoring** - Real-time health checks and metrics

### ✅ Production Features

- **Enterprise Logging** - Structured JSON logs with rotation
- **Health Monitoring** - CPU, memory, disk usage tracking
- **Graceful Shutdown** - Clean resource cleanup
- **Error Handling** - Comprehensive exception management
- **CORS Support** - Cross-origin resource sharing
- **Docker Ready** - Containerized deployment

## Configuration

### Environment Variables

```bash
# API Keys
OPENAI_API_KEY=your-openai-key
GOOGLE_AI_KEY=your-google-ai-key
SERPAPI_KEY=your-serpapi-key

# AGI Mode
AGI_MODE=autonomous  # autonomous, supervised, manual

# Logging
FAME_LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# Data Storage
FAME_DATA_DIR=./fame_data
```

### Config File (`config.yaml`)

See `config.yaml` for full configuration options including:
- Model selection
- Spider settings
- Memory configuration
- Planning parameters
- Reflection settings
- Persona configuration

## Monitoring

### Health Checks

The service exposes health endpoints:
- `/health` - Overall system health
- `/metrics` - Performance metrics

### Logs

Logs are written to:
- Console: Structured format
- File: `logs/agi_core.log`
- JSON: `logs/agi_core.json.log`

### Metrics

Available metrics include:
- Query counts
- Processing times
- Memory usage
- System resources
- Autonomous engine statistics

## Development

### Running Tests

```bash
# Run health check
curl http://localhost:8080/health

# Test query
curl -X POST http://localhost:8080/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, FAME!"}'
```

### Debug Mode

```bash
# Set log level to DEBUG
export FAME_LOG_LEVEL=DEBUG

# Run service
python -m api.fastapi_app
```

## Troubleshooting

### Service Won't Start

1. Check API keys are set: `echo $OPENAI_API_KEY`
2. Verify config file exists: `ls config.yaml`
3. Check logs: `tail -f logs/agi_core.log`

### High Memory Usage

1. Reduce `FAME_CONVO_MAX` in config
2. Enable memory cleanup in autonomous cycle
3. Monitor with `/metrics` endpoint

### Slow Responses

1. Check system metrics: `curl http://localhost:8080/metrics`
2. Verify LLM API keys are valid
3. Check network connectivity

## Next Steps

### Enhancements

1. **FAISS Persistence** - Save/load vector indices
2. **Multi-Agent Spiders** - 50+ concurrent crawlers
3. **Bandit Optimizer** - Real RL algorithm
4. **Secure Secrets** - Vault/AWS Secrets Manager
5. **Kubernetes** - K8s deployment manifests

### Integration

- Connect to frontend applications
- Integrate with message queues
- Add database persistence
- Set up CI/CD pipeline

## Support

For issues or questions:
1. Check logs: `logs/agi_core.log`
2. Review metrics: `/metrics` endpoint
3. Check health: `/health` endpoint

---

**Version:** 6.1  
**Status:** Production Ready  
**Last Updated:** 2024

