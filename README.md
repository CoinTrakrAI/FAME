# 🚀 FAME - Financial AI Market Engine

**FAME** is an advanced AI-powered trading and financial analysis platform that combines real-time market data, machine learning intelligence, and conversational AI to provide comprehensive financial insights and automated trading capabilities.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## ✨ Key Features

- 🤖 **Conversational AI Assistant** - Natural language interface for market queries and analysis
- 📊 **Real-Time Market Data** - Integration with multiple data sources (Alpha Vantage, Finnhub, CoinGecko, SERPAPI)
- 🧠 **Machine Learning Intelligence** - Advanced RL agents and ensemble models for market prediction
- 🎯 **Multi-Asset Support** - Stocks, crypto, forex, and derivatives
- 🐳 **Docker Deployment** - Production-ready containerization for local and cloud deployment
- 🎤 **Voice Interface** - Voice-activated commands and responses
- 📈 **Risk Management** - Advanced risk metrics and portfolio optimization
- 🔄 **Live Training** - Continuous learning from market data and user feedback

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- **Docker Desktop** (optional, for containerized deployment) ([Download](https://www.docker.com/products/docker-desktop/))

### Installation

#### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/CoinTrakrAI/FAME.git
cd FAME

# Copy environment template
cp config/env.example .env
# Edit .env and add your API keys

# Build and run with Docker Compose
docker-compose -f docker-compose.dev.yml up -d

# Access FAME at http://localhost:8080
```

#### Option 2: Local Python Installation

```bash
# Clone the repository
git clone https://github.com/CoinTrakrAI/FAME.git
cd FAME

# Create virtual environment
python -m venv fame_env

# Activate virtual environment
# Windows:
fame_env\Scripts\activate
# Linux/Mac:
source fame_env/bin/activate

# Install dependencies
pip install -r requirements_production.txt

# Copy and configure environment
cp config/env.example .env
# Edit .env with your API keys

# Run FAME
python chat_with_fame.py
```

### Configuration

1. **Copy the environment template:**
   ```bash
   cp config/env.example .env
   ```

2. **Add your API keys** to `.env`:
   ```env
   ALPHA_VANTAGE_KEY=your_key_here
   FINNHUB_KEY=your_key_here
   COINGECKO_KEY=your_key_here
   SERPAPI_KEY=your_key_here
   OPENAI_API_KEY=your_key_here
   ```

   > **Note:** Some features work without API keys using free fallback services (yfinance), but premium features require API keys.

## 📖 Usage Examples

### Chat Interface

```python
# Start interactive chat
python chat_with_fame.py

# Example queries:
# "What's the price of Bitcoin?"
# "Analyze AAPL stock"
# "What's the current market regime?"
# "Show me XRP price predictions"
```

### API Server

```bash
# Start API server
python api/server.py

# Or with Docker
docker-compose up -d

# Test health endpoint
curl http://localhost:8080/healthz
```

### Voice Interface

```bash
# Start voice interface
python fame_voice_main.py
```

## 🐳 Docker Deployment

### Local Development

```bash
docker-compose -f docker-compose.dev.yml up -d
```

### Production (AWS EC2)

```bash
# On your EC2 instance
git clone https://github.com/CoinTrakrAI/FAME.git
cd FAME
cp config/env.example .env
# Edit .env with production API keys

docker-compose -f docker-compose.prod.yml up -d
```

See [DEPLOYMENT_MVP.md](DEPLOYMENT_MVP.md) for detailed deployment instructions.

## 📚 Documentation

- **[Quick Start Guide](QUICK_START.md)** - Get up and running quickly
- **[Desktop Installation](README_Desktop.md)** - Desktop application setup
- **[Production Deployment](DEPLOYMENT_MVP.md)** - Deploy to AWS EC2 or local Docker
- **[Docker Setup Guide](DOCKER_SETUP_GUIDE.md)** - Container configuration
- **[Training Pipeline](docs/TRAINING_PIPELINE.md)** - ML model training
- **[Architecture](PRODUCTION_ARCHITECTURE_BLUEPRINT.md)** - System architecture

## 🏗️ Project Structure

```
FAME/
├── api/                 # REST API server
├── core/                # Core AI engine and modules
│   ├── assistant/       # Conversational AI
│   ├── intelligence/   # ML models and RL agents
│   └── ...
├── services/            # External service integrations
├── training/            # Model training pipelines
├── orchestrator/        # Strategy orchestration
├── monitoring/          # Observability and metrics
├── config/             # Configuration files
├── tests/              # Test suite
└── docker-compose.yml  # Docker configuration
```

## 🔧 Configuration

### Environment Variables

Key environment variables (see `config/env.example`):

- `ALPHA_VANTAGE_KEY` - Alpha Vantage API key
- `FINNHUB_KEY` - Finnhub API key
- `COINGECKO_KEY` - CoinGecko API key
- `SERPAPI_KEY` - SERPAPI for web search
- `OPENAI_API_KEY` - OpenAI API key
- `FAME_ENV` - Environment (development/production)

### Trading Configuration

Edit `config/trading_config.py` to customize:
- Trading strategies
- Risk parameters
- Asset preferences
- Execution settings

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test suite
pytest tests/assistant/
pytest tests/services/
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues:** [GitHub Issues](https://github.com/CoinTrakrAI/FAME/issues)
- **Documentation:** See the `/docs` directory
- **Quick Help:** Check `QUICK_START.md` or `HOW_TO_ASK_FAME.md`

## 🎯 Roadmap

- [ ] Enhanced voice interface
- [ ] Mobile app integration
- [ ] Advanced portfolio optimization
- [ ] Multi-exchange support
- [ ] Social trading features

## 🙏 Acknowledgments

- Built with Python, FastAPI, and modern ML frameworks
- Powered by multiple financial data providers
- Containerized with Docker for easy deployment

---

**Made with ❤️ by the FAME Team**

For more information, visit: https://github.com/CoinTrakrAI/FAME
