#!/usr/bin/env python3
"""
F.A.M.E. Voice-First Desktop Application
Main entry point for voice-driven FAME interface
"""

import sys
import os
import argparse
from pathlib import Path
from voice import VoiceServiceManager, VoiceServiceError


# Fix Unicode for Windows
if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

def check_dependencies():
    """Check and report on required dependencies"""
    required_packages = {
        'customtkinter': 'customtkinter',
        'pillow': 'Pillow',
        'psutil': 'psutil',
        'speechrecognition': 'speechrecognition',
        'pyttsx3': 'pyttsx3',
        'pyaudio': 'pyaudio',
        'pandas': 'pandas',
        'yfinance': 'yfinance',
        'numpy': 'numpy'
    }
    
    missing_required = []
    missing_optional = []
    
    for package, install_name in required_packages.items():
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            if package in ['speechrecognition', 'pyttsx3', 'pyaudio']:
                missing_optional.append(install_name)
            else:
                missing_required.append(install_name)
    
    if missing_required:
        print("=" * 60)
        print("❌ MISSING REQUIRED DEPENDENCIES:")
        print("=" * 60)
        for pkg in missing_required:
            print(f"   - {pkg}")
        print("\nInstall with:")
        print(f"   pip install {' '.join(missing_required)}")
        print("=" * 60)
        return False
    
    if missing_optional:
        print(f"\n⚠️  Missing optional dependencies: {', '.join(missing_optional)}")
        print("   Some voice features may be limited.")
        print("   Install with: pip install " + " ".join(missing_optional))
    
    return True


def run_diagnostics() -> int:
    manager = VoiceServiceManager()
    print("Voice configuration summary:")
    for key, value in manager.config_summary().items():
        print(f"  {key}: {value}")
    metrics = manager.telemetry_snapshot()
    print("Telemetry (current session):")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    try:
        devices = manager.list_audio_devices()
        if not devices:
            print("No input devices detected.")
        else:
            print("Available input devices:")
            for index, name in devices.items():
                print(f"  [{index}] {name}")
    except VoiceServiceError as exc:
        print(f"Device enumeration failed: {exc}")
        return 1
    return 0


def main():
    """Launch F.A.M.E. Voice-First Interface"""

    parser = argparse.ArgumentParser(description="FAME enterprise voice launcher")
    parser.add_argument("--diagnostics", action="store_true", help="Run voice diagnostics and exit")
    parser.add_argument("--list-devices", action="store_true", help="List available audio input devices")
    args = parser.parse_args()

    if args.diagnostics or args.list_devices:
        rc = run_diagnostics()
        if args.list_devices and not args.diagnostics:
            # Diagnostics already list devices; avoid double printing
            pass
        return rc
    print("=" * 60)
    print("🚀 F.A.M.E. - Cosmic Voice Intelligence")
    print("=" * 60)
    print("Initializing F.A.M.E. System...")
    print("Loading advanced modules...")
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install required dependencies first.")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # Add to path
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        # Try importing the voice-enhanced interface
        try:
            from ui.functional_interface_voice import VoiceEnhancedInterface
            print("\n✅ Loading Voice-Enhanced Interface...")
            app = VoiceEnhancedInterface()
        except ImportError:
            print("\n⚠️  Voice-enhanced interface not found, loading standard interface...")
            from ui.functional_interface import FunctionalInterface
            app = FunctionalInterface()
        
        print("\n✅ F.A.M.E. successfully launched!")
        print("\n" + "=" * 60)
        print("Features Available:")
        print("   - Voice-first interaction")
        print("   - Advanced investment AI")
        print("   - Market prediction & analysis")
        print("   - Universal hacking capabilities")
        print("   - Full-stack development")
        print("   - Cloud dominance")
        print("   - Self-evolving AI")
        print("=" * 60)
        print("\nSpeak to FAME or type commands in the chat interface.")
        print("Say 'Hello FAME' to begin!\n")
        
        app.mainloop()
        
    except Exception as e:
        print(f"\n❌ Launch error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())

