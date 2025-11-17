# 🖥️ FAME Desktop Application - User Guide

## 🚀 **Quick Start**

### **Option 1: Run from Source (Development)**

```bash
# Install dependencies
pip install -r requirements_production.txt
pip install PyQt5  # For desktop GUI

# Run the desktop app
python fame_desktop_app.py
```

### **Option 2: Run Executable (Production)**

1. **Download** `FAME_Desktop.exe` from the `dist/` folder
2. **Double-click** to run
3. **First time setup:**
   - Install Docker Desktop (if not already installed)
   - Start Docker Desktop
   - LocalAI will start automatically

---

## 📋 **Features**

### **💰 Finance-First AI**
- **Real-time Prices:** Stocks, crypto, commodities, ETFs
- **Comprehensive Analysis:** Technical and fundamental analysis
- **Trading Strategies:** Day trading, swing trading, position trading guidance
- **Market Predictions:** Price forecasts and trend analysis
- **Risk Assessment:** Portfolio risk metrics

### **🎤 Voice Interface**
- **Speech-to-Text:** Talk to FAME naturally
- **Text-to-Speech:** FAME responds with voice
- **Push-to-Talk:** Hold microphone button to speak

### **🧠 Living System**
- **Self-Learning:** Learns from every interaction
- **Self-Healing:** Automatically fixes issues
- **Goal-Driven:** Pursues optimization goals
- **Memory System:** Remembers past interactions

### **🐳 LocalAI Integration**
- **Local Inference:** Run AI models locally
- **Privacy:** Your data never leaves your machine
- **No Internet Required:** Works offline (after initial setup)

---

## 🛠️ **Setup Instructions**

### **1. Install Docker Desktop**

1. Download from: https://www.docker.com/products/docker-desktop/
2. Install and start Docker Desktop
3. Verify: Open terminal and run `docker --version`

### **2. Start LocalAI (Optional but Recommended)**

**Automatic (via GUI):**
- FAME Desktop will attempt to start LocalAI automatically
- Check status in menu: Tools → LocalAI Status

**Manual:**
```bash
# CPU version
docker run -d --name local-ai -p 8080:8080 localai/localai:latest

# NVIDIA GPU version (if you have NVIDIA GPU)
docker run -d --name local-ai -p 8080:8080 --gpus all localai/localai:latest-gpu-nvidia-cuda-12
```

### **3. Configure API Keys (Optional)**

API keys are pre-configured for demo purposes. To use your own:

1. Create `.env` file in the FAME directory
2. Copy from `config/env.example`
3. Add your API keys

**Required for full functionality:**
- Alpha Vantage (stock data)
- CoinGecko (crypto data)
- Finnhub (real-time quotes)
- OpenAI or LocalAI (AI responses)

---

## 💬 **Usage Examples**

### **Stock Queries**
```
"What's the price of AAPL?"
"Analyze TSLA stock"
"Should I buy MSFT?"
"Show me GOOGL analysis"
```

### **Crypto Queries**
```
"What's the price of Bitcoin?"
"Analyze XRP"
"Ethereum price prediction"
"What's SOL trading at?"
```

### **Trading Strategies**
```
"Day trading strategies"
"Swing trading for beginners"
"Best swing trading stocks"
"Options trading basics"
```

### **Market Analysis**
```
"Market analysis today"
"Best stocks to buy now"
"Crypto market sentiment"
"Stock market predictions"
```

---

## 🎯 **Key Features Explained**

### **Finance-First Routing**
FAME prioritizes financial queries and provides comprehensive analysis:
- Real-time prices from multiple sources
- Technical indicators (RSI, MACD, moving averages)
- Volume analysis
- Price trends and patterns
- Trading recommendations framework

### **Living System**
The system learns and adapts:
- **Memory:** Stores successful interactions
- **Perception:** Monitors system health and performance
- **Goals:** Pursues optimization objectives
- **Healing:** Automatically fixes issues

### **LocalAI Integration**
- Runs AI models locally in Docker
- No data sent to external servers
- Works offline after initial setup
- Supports multiple model types

---

## 🔧 **Troubleshooting**

### **LocalAI Not Starting**
1. Check Docker Desktop is running
2. Verify port 8080 is not in use
3. Check Docker logs: `docker logs local-ai`
4. Try manual start (see Setup Instructions)

### **Voice Not Working**
1. Check microphone permissions
2. Verify audio drivers are installed
3. Try different microphone in settings
4. Check Windows audio settings

### **API Errors**
1. Verify API keys in `.env` file
2. Check internet connection
3. Some APIs have rate limits - wait and retry
4. Free APIs (yfinance) work without keys

### **Application Won't Start**
1. Check Python version (3.8+)
2. Install dependencies: `pip install -r requirements_production.txt`
3. Install PyQt5: `pip install PyQt5`
4. Check logs in `fame_desktop.log`

---

## 📦 **Building from Source**

### **Requirements**
- Python 3.8+
- PyInstaller
- All dependencies from `requirements_production.txt`

### **Build Steps**
```bash
# Install build dependencies
pip install pyinstaller

# Run build script
python build_desktop_exe.py

# Executable will be in dist/FAME_Desktop.exe
```

---

## 🎨 **Customization**

### **Themes**
- Dark theme (default)
- Light theme (coming soon)
- Custom themes (coming soon)

### **Settings**
Access via: File → Settings
- API key configuration
- LocalAI endpoint
- Voice settings
- Theme selection

---

## 📞 **Support**

- **Issues:** Check `fame_desktop.log` for errors
- **Documentation:** See `FAME_DESKTOP_BLUEPRINT.md`
- **GitHub:** https://github.com/CoinTrakrAI/FAME

---

## ⚠️ **Important Notes**

1. **Not Financial Advice:** All recommendations are for informational purposes only
2. **API Keys:** Keep your API keys secure and never share them
3. **Docker Required:** LocalAI requires Docker Desktop
4. **Internet:** Some features require internet connection (API calls)

---

**Enjoy using FAME Desktop! 🚀💰**

