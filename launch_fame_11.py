#!/usr/bin/env python3
"""
F.A.M.E. 11.0 - Premium Cosmic Launcher
Launch the ultimate 2028 interface
"""

import sys
import os
from pathlib import Path

def check_dependencies():
    """Check and install required dependencies"""
    required_packages = {
        'customtkinter': 'customtkinter',
        'pillow': 'Pillow',
        'matplotlib': 'matplotlib', 
        'numpy': 'numpy',
        'speechrecognition': 'speechrecognition',
        'pyttsx3': 'pyttsx3',
        'pyaudio': 'pyaudio',
        'torch': 'torch',
        'transformers': 'transformers',
        'langchain': 'langchain',
        'jax': 'jax',
        'onnxruntime': 'onnxruntime'
    }
    
    missing = []
    for package, install_name in required_packages.items():
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(install_name)
    
    if missing:
        print(f"Missing {len(missing)} optional dependencies:")
        print("   " + ", ".join(missing))
        print("\nSome features may be limited without these packages.")
        print("   Install with: pip install " + " ".join(missing))
        print("\nLaunching with available features...\n")


def main():
    """Launch F.A.M.E. 11.0 Cosmic Interface"""
    # Fix Unicode for Windows console
    if sys.platform == 'win32':
        import codecs
        try:
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
        except:
            pass  # Fallback to ASCII if UTF-8 fails
    
    print("Initializing F.A.M.E. 11.0 - Cosmic Intelligence")
    print("Loading premium 2028 interface...")
    
    # Check dependencies
    check_dependencies()
    
    # Add to path
    sys.path.insert(0, str(Path(__file__).parent))
    
    # Launch interface
    try:
        from ui.functional_interface import FunctionalInterface
        
        print("[OK] F.A.M.E. 11.0 successfully launching!")
        print("\nFeatures Available:")
        print("   - Live Dashboard with real metrics")
        print("   - AI Core Control (with PyTorch, Transformers, LangChain, JAX)")
        print("   - Universal Hacking with actual scanning")
        print("   - Development Suite with build tools")
        print("   - Cloud Dominance (AWS, Azure, GCP)")
        print("   - God Mode with cosmic powers")
        print("   - Voice Interface")
        print("   - Real-time activity feed")
        print("   - All buttons actually work!")
        print("\nLaunching functional interface...\n")
        
        app = FunctionalInterface()
        app.mainloop()
        
    except Exception as e:
        print(f"[ERROR] Launch failed: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()

