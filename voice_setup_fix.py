#!/usr/bin/env python3
"""
Voice Setup Helper - Fixes voice recognition installation issues
This addresses the F.A.M.E 6.0 voice issue and ensures it works in 7.0/8.0
"""

import subprocess
import sys
import os
import platform
from pathlib import Path


def install_voice_dependencies():
    """Install voice recognition dependencies with proper error handling"""
    
    print("=" * 60)
    print("F.A.M.E Voice Setup - Fixing Voice Recognition")
    print("=" * 60)
    print()
    
    # Step 1: Install SpeechRecognition
    print("[1/4] Installing SpeechRecognition...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "SpeechRecognition"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("   ✅ SpeechRecognition installed")
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Step 2: Install pyttsx3
    print("[2/4] Installing pyttsx3 (Text-to-Speech)...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyttsx3"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("   ✅ pyttsx3 installed")
    except subprocess.CalledProcessError as e:
        print(f"   ⚠️ Warning: pyttsx3 installation had issues: {e}")
    
    # Step 3: Install PyAudio (the tricky one)
    print("[3/4] Installing PyAudio (this is the difficult one)...")
    
    system = platform.system()
    
    if system == "Windows":
        install_pyaudio_windows()
    elif system == "Darwin":  # macOS
        install_pyaudio_mac()
    elif system == "Linux":
        install_pyaudio_linux()
    else:
        print(f"   ⚠️ Unknown system: {system}, trying standard pip install...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "PyAudio"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("   ✅ PyAudio installed")
        except:
            print("   ❌ PyAudio installation failed")
            print_manual_instructions()
    
    # Step 4: Verify installation
    print("[4/4] Verifying installation...")
    verify_voice_installation()
    
    print()
    print("=" * 60)
    print("✅ Voice setup complete!")
    print("=" * 60)
    print()
    print("You can now use voice features in F.A.M.E!")
    print("Try enabling voice in the desktop application.")


def install_pyaudio_windows():
    """Install PyAudio on Windows (most problematic)"""
    print("   Detected Windows - using pipwin method...")
    
    # Method 1: Try pipwin (recommended for Windows)
    try:
        # Install pipwin first
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pipwin"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Use pipwin to install PyAudio
        subprocess.check_call([sys.executable, "-m", "pipwin", "install", "pyaudio"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("   ✅ PyAudio installed via pipwin")
        return True
    except:
        print("   ⚠️ pipwin method failed, trying alternatives...")
    
    # Method 2: Try direct pip install
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyAudio"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("   ✅ PyAudio installed via pip")
        return True
    except:
        print("   ⚠️ Direct pip install failed")
    
    # Method 3: Manual wheel installation instructions
    print("   ❌ Automatic installation failed")
    print_manual_windows_instructions()
    return False


def install_pyaudio_mac():
    """Install PyAudio on macOS"""
    print("   Detected macOS - installing via Homebrew + pip...")
    
    try:
        # Install portaudio via Homebrew
        subprocess.check_call(["brew", "install", "portaudio"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Then install PyAudio
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyAudio"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("   ✅ PyAudio installed")
        return True
    except:
        print("   ⚠️ Installation failed - Homebrew may not be installed")
        print("   Install Homebrew first: https://brew.sh")
        return False


def install_pyaudio_linux():
    """Install PyAudio on Linux"""
    print("   Detected Linux - installing system dependencies...")
    
    try:
        # Install portaudio dev package
        subprocess.check_call(["sudo", "apt-get", "install", "-y", "portaudio19-dev"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Then install PyAudio
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyAudio"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("   ✅ PyAudio installed")
        return True
    except:
        print("   ⚠️ Installation failed - may need sudo permissions")
        return False


def verify_voice_installation():
    """Verify that all voice libraries are installed"""
    print("   Testing imports...")
    
    errors = []
    
    # Test SpeechRecognition
    try:
        import speech_recognition as sr
        print("   ✅ SpeechRecognition: OK")
    except ImportError:
        errors.append("SpeechRecognition")
        print("   ❌ SpeechRecognition: NOT INSTALLED")
    
    # Test pyttsx3
    try:
        import pyttsx3
        print("   ✅ pyttsx3: OK")
    except ImportError:
        errors.append("pyttsx3")
        print("   ❌ pyttsx3: NOT INSTALLED")
    
    # Test PyAudio
    try:
        import pyaudio
        print("   ✅ PyAudio: OK")
    except ImportError:
        errors.append("PyAudio")
        print("   ❌ PyAudio: NOT INSTALLED")
        print("   ⚠️ Voice input will not work without PyAudio")
    
    if errors:
        print()
        print("   ⚠️ Some libraries are missing:")
        for lib in errors:
            print(f"      - {lib}")
        print()
        print("   Voice features will have limited functionality.")
        print("   See manual installation instructions below.")
    else:
        print()
        print("   ✅ All voice libraries are installed and working!")


def print_manual_windows_instructions():
    """Print manual installation instructions for Windows"""
    print()
    print("=" * 60)
    print("MANUAL INSTALLATION INSTRUCTIONS (Windows)")
    print("=" * 60)
    print()
    print("PyAudio requires a pre-compiled wheel for Windows.")
    print()
    print("Step 1: Find your Python version:")
    print(f"   Your Python: {sys.version}")
    print()
    print("Step 2: Download matching wheel from:")
    print("   https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio")
    print()
    print("Step 3: Install the downloaded wheel:")
    print("   pip install PyAudio‑0.2.11‑cp<version>‑cp<version>‑win_amd64.whl")
    print()
    print("Example for Python 3.11 (64-bit):")
    print("   pip install PyAudio‑0.2.11‑cp311‑cp311‑win_amd64.whl")
    print()


def print_manual_instructions():
    """Print general manual instructions"""
    print()
    print("=" * 60)
    print("ALTERNATIVE: Manual Installation")
    print("=" * 60)
    print()
    print("If automatic installation fails:")
    print()
    print("Windows:")
    print("  1. Download wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio")
    print("  2. pip install <downloaded_wheel_file>.whl")
    print()
    print("macOS:")
    print("  1. Install Homebrew: https://brew.sh")
    print("  2. brew install portaudio")
    print("  3. pip install PyAudio")
    print()
    print("Linux:")
    print("  1. sudo apt-get install portaudio19-dev")
    print("  2. pip install PyAudio")
    print()


def create_voice_test_script():
    """Create a test script to verify voice works"""
    test_script = """#!/usr/bin/env python3
\"\"\"Test voice recognition and TTS\"\"\"

print("Testing voice libraries...")

# Test 1: SpeechRecognition
try:
    import speech_recognition as sr
    r = sr.Recognizer()
    print("✅ SpeechRecognition: Working")
except Exception as e:
    print(f"❌ SpeechRecognition: {e}")

# Test 2: PyAudio
try:
    import pyaudio
    p = pyaudio.PyAudio()
    device_count = p.get_device_count()
    print(f"✅ PyAudio: Working ({device_count} audio devices found)")
    p.terminate()
except Exception as e:
    print(f"❌ PyAudio: {e}")

# Test 3: TTS
try:
    import pyttsx3
    engine = pyttsx3.init()
    print("✅ pyttsx3: Working")
except Exception as e:
    print(f"❌ pyttsx3: {e}")

print()
print("Voice test complete!")
"""
    
    test_file = Path("test_voice.py")
    with open(test_file, 'w') as f:
        f.write(test_script)
    
    print(f"📄 Created test script: {test_file}")
    print("   Run it with: python test_voice.py")


if __name__ == "__main__":
    print()
    install_voice_dependencies()
    print()
    create_voice_test_script()
    print()
    print("🎉 Setup complete! Voice features should now work in F.A.M.E 8.0")

