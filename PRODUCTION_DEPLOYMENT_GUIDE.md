# FAME Production Deployment Guide

## Quick Start

### 1. Installation

```bash
# Install production dependencies
pip install -r requirements_production.txt

# Install pyaudio for voice (OS-specific)
# Windows:
pip install pipwin
pipwin install pyaudio

# Linux:
sudo apt-get install portaudio19-dev
pip install pyaudio

# Mac:
brew install portaudio
pip install pyaudio
```

### 2. Configuration

Set up API keys in `fame_config.py` or environment variables:

```bash
export SERPAPI_KEY="your_serpapi_key"
export ALPHA_VANTAGE_API_KEY="your_alpha_vantage_key"
export FINNHUB_API_KEY="your_finnhub_key"
```

### 3. Run FAME

#### Option A: Unified Entry Point (Recommended)
```bash
python fame_unified.py
```

#### Option B: Desktop GUI
```bash
python fame_desktop.py
```

#### Option C: Chat Interface
```bash
python fame_chat_ui.py
```

## Architecture Overview

### Core Components

1. **FAME Unified** (`fame_unified.py`)
   - Main entry point for all interfaces
   - Handles routing, decision-making, and response synthesis

2. **Autonomous Decision Engine** (`core/autonomous_decision_engine.py`)
   - Intent classification
   - Module selection with confidence scoring
   - Response synthesis

3. **Brain Orchestrator** (`orchestrator/brain.py`)
   - Module execution
   - Plugin management
   - Event bus integration

4. **Health Monitor** (`core/health_monitor.py`)
   - System health tracking
   - Performance metrics
   - Module status monitoring

5. **Production Logger** (`core/production_logger.py`)
   - Structured logging
   - Error tracking
   - Audit trails

## Features

### Autonomous Decision-Making
- **Intent Classification**: Automatically determines user intent
- **Confidence Scoring**: Every decision includes confidence metrics
- **Multi-Module Routing**: Routes to appropriate modules based on query
- **Response Synthesis**: Combines multiple responses when needed

### Communication Modes
- **Voice**: Natural language voice input/output
- **Text**: Chat-based interaction
- **GUI**: Desktop application with real-time status
- **API**: RESTful API (future)

### Module Integration
- **Plugin Architecture**: Hot-swappable modules
- **Event-Driven**: Pub/sub event bus
- **Graceful Degradation**: Works even if some modules fail

## Monitoring

### Health Checks
```python
from fame_unified import get_fame

fame = get_fame()
health = fame.get_health_status()
print(health['overall_status'])  # healthy, degraded, or unhealthy
```

### Performance Metrics
```python
metrics = fame.get_performance_metrics()
print(f"Average response time: {metrics['average_response_time']:.2f}s")
```

### Logs
Logs are stored in `logs/` directory:
- `fame_YYYYMMDD.log` - General logs
- `fame_errors_YYYYMMDD.log` - Error logs

## Troubleshooting

### Module Not Loading
- Check if module file exists in `core/` directory
- Verify module has proper `handle()` method
- Check logs for import errors

### API Errors
- Verify API keys are set correctly
- Check network connectivity
- Review API quota limits

### Performance Issues
- Check system resources (CPU, memory)
- Review response times in metrics
- Check for module failures in health status

## Production Considerations

### Security
- Store API keys securely (use environment variables)
- Enable authentication for API access (future)
- Review audit logs regularly

### Performance
- Monitor response times
- Set up alerts for degraded performance
- Scale resources as needed

### Reliability
- Implement health checks
- Set up automatic recovery
- Monitor error rates

## Next Steps

1. **Customize Modules**: Add domain-specific modules
2. **Configure APIs**: Set up required API keys
3. **Test Thoroughly**: Run through various query types
4. **Monitor Performance**: Track metrics and optimize
5. **Deploy**: Set up production environment

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review health status
3. Check module status
4. Review error messages

