# FAME - Production-Ready AI Assistant

## 🚀 Overview

FAME (Fully Autonomous Machine Entity) is a production-ready, enterprise-grade AI assistant comparable to Siri or Alexa. It features:

- **Autonomous Decision-Making**: Intelligent routing with confidence scoring
- **Multi-Modal Communication**: Voice, text, and GUI interfaces
- **Production-Grade Infrastructure**: Health monitoring, structured logging, error recovery
- **Fintech Standards**: OWASP-compliant security, comprehensive audit trails
- **Hot-Swappable Modules**: Plugin architecture for easy extension

## ✨ Key Features

### 1. Autonomous Decision Engine
- Intent classification with NLP
- Confidence-based routing (0.0-1.0)
- Multi-module response synthesis
- Context-aware conversations

### 2. Production Infrastructure
- **Health Monitoring**: Real-time system status tracking
- **Structured Logging**: JSON logs with audit trails
- **Performance Metrics**: Response time tracking, error rates
- **Error Recovery**: Graceful degradation and fallbacks

### 3. Communication Modes
- **Voice Interface**: Natural language voice I/O
- **Text Chat**: Interactive chat interface
- **Desktop GUI**: Full-featured desktop application
- **API Ready**: RESTful API architecture (future)

### 4. Core Capabilities
- **Financial Analysis**: Stock market, crypto, investment insights
- **Technical Q&A**: Software development, architecture, security
- **Real-Time Information**: Web search integration
- **Knowledge Base**: Book-based learning and retrieval
- **Code Generation**: Development assistance
- **Security Analysis**: Cybersecurity and hacking (gated)

## 📋 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements_production.txt

# Install voice dependencies (OS-specific)
# Windows:
pip install pipwin && pipwin install pyaudio

# Linux:
sudo apt-get install portaudio19-dev && pip install pyaudio

# Mac:
brew install portaudio && pip install pyaudio
```

### Configuration

Set up API keys in `fame_config.py` or environment variables:

```bash
export SERPAPI_KEY="your_key"
export ALPHA_VANTAGE_API_KEY="your_key"
export FINNHUB_API_KEY="your_key"
```

### Run FAME

**Option 1: Unified Entry Point (Recommended)**
```bash
python fame_unified.py
```

**Option 2: Desktop GUI**
```bash
python fame_desktop.py
```

**Option 3: Chat Interface**
```bash
python fame_chat_ui.py
```

## 🏗️ Architecture

```
User Input (Voice/Text/GUI)
    ↓
FAME Unified Entry Point
    ↓
Autonomous Decision Engine
    ├─ Intent Classification
    ├─ Confidence Scoring
    └─ Module Selection
    ↓
Brain Orchestrator
    ├─ Module Execution
    ├─ Response Aggregation
    └─ Error Handling
    ↓
Health Monitor + Production Logger
    ↓
Response to User
```

### Core Components

1. **`fame_unified.py`** - Main entry point
2. **`core/autonomous_decision_engine.py`** - Decision-making engine
3. **`orchestrator/brain.py`** - Module orchestration
4. **`core/health_monitor.py`** - System health tracking
5. **`core/production_logger.py`** - Structured logging

### Module Categories

- **Knowledge & Q&A**: `qa_engine`, `web_scraper`, `knowledge_base`
- **Financial**: `advanced_investor_ai`, `enhanced_market_oracle`
- **Development**: `universal_developer`, `docker_manager`
- **Security**: `universal_hacker` (gated)
- **Specialized**: `consciousness_engine`, `evolution_engine`

## 📊 Monitoring & Health

### Check System Health

```python
from fame_unified import get_fame

fame = get_fame()
health = fame.get_health_status()

print(f"Status: {health['overall_status']}")
print(f"Warnings: {len(health.get('warnings', []))}")
print(f"Errors: {len(health.get('errors', []))}")
```

### Performance Metrics

```python
metrics = fame.get_performance_metrics()
print(f"Avg Response Time: {metrics['average_response_time']:.2f}s")
print(f"P95 Response Time: {metrics['p95_response_time']:.2f}s")
```

### Logs

Logs are stored in `logs/`:
- `fame_YYYYMMDD.log` - General logs
- `fame_errors_YYYYMMDD.log` - Error logs

## 🔒 Security

- **Input Validation**: All inputs sanitized
- **API Key Management**: Secure storage and rotation
- **Audit Logging**: Complete action tracking
- **Sandbox Execution**: Code runs in isolated containers
- **Dangerous Capability Gating**: Security features require approval

## 🎯 Example Queries

### Financial
```
"Analyze Apple stock"
"What's Bitcoin's current price?"
"Stock market forecast for next week"
```

### Technical
```
"How to build a reverse proxy?"
"Compare Nginx vs Envoy vs HAProxy"
"Create a Python API server"
```

### General Knowledge
```
"Who is the current US president?"
"What is machine learning?"
"Explain quantum computing"
```

### Security
```
"Ransomware containment steps"
"SQL injection prevention"
"Network security best practices"
```

## 📈 Performance Targets

- **Response Time**: < 5 seconds for 95% of queries
- **Uptime**: 99% (excluding planned maintenance)
- **Confidence**: High confidence (≥80%) for most queries
- **Error Rate**: < 1% for production queries

## 🛠️ Development

### Adding a New Module

1. Create module in `core/` directory
2. Implement `handle(query: Dict) -> Dict` method
3. Module auto-discovers on startup
4. Configure routing in decision engine

### Testing

```bash
# Run tests
pytest tests/

# Test specific module
python -m pytest tests/test_qa_engine.py
```

## 📚 Documentation

- **Architecture Blueprint**: `PRODUCTION_ARCHITECTURE_BLUEPRINT.md`
- **Deployment Guide**: `PRODUCTION_DEPLOYMENT_GUIDE.md`
- **Module Documentation**: See individual module files

## 🐛 Troubleshooting

### Module Not Loading
- Check module exists in `core/`
- Verify `handle()` method exists
- Check logs for import errors

### API Errors
- Verify API keys configured
- Check network connectivity
- Review API quota limits

### Performance Issues
- Check system resources (CPU/memory)
- Review response times in metrics
- Check module health status

## 🚀 Production Deployment

### Prerequisites
- Python 3.8+
- All dependencies installed
- API keys configured
- Docker (optional, for sandboxing)

### Steps
1. Install dependencies: `pip install -r requirements_production.txt`
2. Configure API keys
3. Run health checks: `python -c "from fame_unified import get_fame; print(get_fame().get_health_status())"`
4. Start FAME: `python fame_unified.py`

### Monitoring
- Monitor logs in `logs/` directory
- Check health status regularly
- Track performance metrics
- Review error rates

## 📝 License

See LICENSE file for details.

## 🤝 Contributing

Contributions welcome! Please:
1. Follow code style guidelines
2. Add tests for new features
3. Update documentation
4. Submit pull requests

## 📞 Support

For issues:
1. Check logs in `logs/` directory
2. Review health status
3. Check module status
4. Review error messages

---

**FAME** - Fully Autonomous Machine Entity  
*Production-Ready AI Assistant*

