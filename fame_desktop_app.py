#!/usr/bin/env python3
"""
FAME Desktop Application - Main Entry Point
Integrates Living System + Finance-First + Desktop GUI + LocalAI
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fame_desktop.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def initialize_living_system():
    """Initialize and start the living system in background"""
    try:
        from core.living_system import FAMELivingSystem
        
        async def start_living_system():
            living_fame = FAMELivingSystem(
                openai_api_key=os.getenv('OPENAI_API_KEY'),
                enable_voice=os.getenv('ENABLE_VOICE', 'true').lower() == 'true'
            )
            await living_fame.awaken_system()
            return living_fame
        
        # Start in background thread
        def run_living_system():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                living_system = loop.run_until_complete(start_living_system())
                loop.run_forever()
            except Exception as e:
                logger.error(f"Living system error: {e}")
            finally:
                loop.close()
        
        import threading
        living_thread = threading.Thread(target=run_living_system, daemon=True)
        living_thread.start()
        logger.info("Living system started in background")
        return True
    except Exception as e:
        logger.warning(f"Could not start living system: {e}")
        return False


def ensure_localai():
    """Ensure LocalAI is running"""
    try:
        from core.localai_manager import get_localai_manager
        manager = get_localai_manager()
        
        status = manager.get_status()
        if not status['api_healthy']:
            logger.info("LocalAI not running, attempting to start...")
            result = manager.start_localai()
            if result.get('success'):
                logger.info("LocalAI started successfully")
                return True
            else:
                logger.warning(f"Could not start LocalAI: {result.get('message')}")
                return False
        else:
            logger.info("LocalAI is already running")
            return True
    except Exception as e:
        logger.warning(f"LocalAI check failed: {e}")
        return False


def main():
    """Main entry point"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║   FAME - Financial AI Market Engine                     ║
    ║   Version 6.0 - Living System + Desktop GUI             ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Initialize living system
    print("🌱 Initializing living system...")
    living_system_started = initialize_living_system()
    if living_system_started:
        print("✅ Living system awakened")
    else:
        print("⚠️ Living system not available (continuing anyway)")
    
    # Check LocalAI
    print("🐳 Checking LocalAI...")
    localai_ready = ensure_localai()
    if localai_ready:
        print("✅ LocalAI is ready")
    else:
        print("⚠️ LocalAI not available (will use OpenAI if configured)")
    
    # Launch desktop GUI
    print("🖥️ Launching desktop interface...")
    try:
        from ui.desktop.main_window import main as gui_main
        gui_main()
    except ImportError as e:
        logger.error(f"Failed to import desktop GUI: {e}")
        print("❌ Desktop GUI not available")
        print("Please install PyQt5: pip install PyQt5")
        print("Or use the command-line interface: python chat_with_fame.py")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to launch desktop GUI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

