# 🚀 F.A.M.E 6.0 Desktop Application

Complete desktop application with voice interface and Docker-based training platform.

## 📦 Installation

### Quick Install (Windows)

1. **Run the installer:**
   ```batch
   install_fame.bat
   ```

2. **Or manual installation:**
   ```bash
   # Create virtual environment
   python -m venv fame_env
   
   # Activate virtual environment
   # Windows:
   fame_env\Scripts\activate
   # Linux/Mac:
   source fame_env/bin/activate
   
   # Install dependencies
   pip install -r requirements_desktop.txt
   ```

### Prerequisites

- **Python 3.8+** (https://www.python.org/downloads/)
- **Docker Desktop** (optional, for LocalAI and training) (https://www.docker.com/products/docker-desktop/)
- **Microphone** (for voice interface)

## 🚀 Quick Start

### Method 1: Desktop Shortcut
- Double-click "FAME_Launcher" on your desktop (created by installer)

### Method 2: Command Line
```bash
# Activate virtual environment
fame_env\Scripts\activate

# Run application
python fame_desktop.py
```

## 🎯 Features

✅ **Complete Desktop GUI** - No command line needed  
✅ **Voice Interface** - Talk naturally with the AI  
✅ **Docker Integration** - Automatic LocalAI setup  
✅ **Visual Training Interface** - Train models with GUI  
✅ **Real-time Monitoring** - Watch system vital signs  
✅ **One-Click Deployment** - Simple installer  

## 📖 Usage

### Starting the Application

1. Launch `fame_desktop.py` or use the desktop shortcut
2. Click "🤖 Start LocalAI" to start the AI backend (if using Docker)
3. Click "🎤 Enable Voice" for voice interaction
4. Click "🚀 Start F.A.M.E" to awaken the system

### Voice Interaction

- Click "🎤 Voice Input" or press the microphone button
- Speak naturally - the system will respond verbally
- Ask questions like:
  - "Hello, how are you today?"
  - "What's the current market status?"
  - "Start training session"
  - "Tell me about your capabilities"

### Training Interface

1. Click "🧠 Open Training" in the main interface
2. Select model and parameters
3. Click "Start Training"
4. Monitor real-time progress with graphs
5. View training metrics and visualizations

## 🐳 Docker Setup

### Starting LocalAI

The application can automatically manage LocalAI via Docker:

1. Ensure Docker Desktop is running
2. Click "🤖 Start LocalAI" in the application
3. Wait for container to start (~30 seconds)
4. LocalAI will be available at `http://localhost:8080`

### Manual Docker Commands

```bash
# Start all services
docker-compose up -d

# Start only LocalAI
docker-compose up -d localai

# Start training environment
docker-compose --profile training up -d training-environment

# Stop all services
docker-compose down

# View logs
docker-compose logs -f localai
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the FAME_Desktop folder:

```env
USE_LOCALAI=true
LOCALAI_ENDPOINT=http://localhost:8080
OPENAI_API_KEY=your_key_here (if not using LocalAI)
```

### API Keys

For full functionality, configure API keys in the parent F.A.M.E system's `.env` file:
- CoinGecko API
- Alpha Vantage API
- Finnhub API
- GNews API
- NewsAPI

## 🛠️ Troubleshooting

### Issue: "Python not found"
- **Solution**: Install Python 3.8+ and add it to PATH

### Issue: "Docker not available"
- **Solution**: Install Docker Desktop from docker.com
- The application will work with limited features without Docker

### Issue: "Voice not working"
- **Solution**: 
  1. Check microphone permissions in Windows Settings
  2. Install PyAudio: `pip install pipwin && pipwin install pyaudio`
  3. Or use alternative: `pip install pyaudio` (may need Visual C++ build tools)

### Issue: "LocalAI connection failed"
- **Solution**: 
  1. Ensure Docker Desktop is running
  2. Click "🤖 Start LocalAI" button
  3. Wait 30-60 seconds for container to start
  4. Check logs: `docker-compose logs localai`

### Issue: "Module not found"
- **Solution**: Install missing module: `pip install <module_name>`

### Issue: "Matplotlib plots not showing"
- **Solution**: Install matplotlib: `pip install matplotlib numpy`

## 📁 Directory Structure

```
FAME_Desktop/
├── fame_desktop.py          # Main application
├── docker-compose.yml        # Docker configuration
├── requirements_desktop.txt  # Python dependencies
├── install_fame.bat          # Installer script
├── LocalAI_Config/
│   └── models/               # LocalAI model files
├── Training_Interface/
│   ├── training_gui.py       # Training GUI
│   └── model_manager.py      # Model management
└── Voice_Interface/
    ├── voice_app.py          # Voice interface
    └── audio_processing/     # Audio utilities
```

## 🔐 Security Notes

- Keep your `.env` file private (contains API keys)
- Don't share API keys
- Docker containers run locally only
- No data sent to external servers except configured APIs

## 📝 Notes

- **First launch**: May take 10-30 seconds to initialize
- **Voice recognition**: Requires internet connection (uses Google Speech API)
- **Training**: Requires significant disk space for models
- **LocalAI**: First model download can take time depending on model size

## 🆘 Support

For issues:
1. Check the application logs in the console
2. Verify Docker Desktop is running (if using LocalAI)
3. Ensure all dependencies are installed: `pip install -r requirements_desktop.txt`
4. Check Python version: `python --version` (should be 3.8+)

## 🎉 Enjoy!

You now have a complete desktop application for F.A.M.E 6.0 - a living AI system you can interact with naturally through voice and GUI!

