#!/usr/bin/env python3
"""
Quick test script for F.A.M.E Desktop before building .exe
Tests imports and basic functionality
"""

import sys
from pathlib import Path

print("=" * 60)
print("F.A.M.E 6.0 Desktop - Pre-Build Test")
print("=" * 60)
print()

errors = []
warnings = []

# Test 1: Python version
print("[1/7] Testing Python version...")
if sys.version_info < (3, 8):
    errors.append(f"Python 3.8+ required. Found: {sys.version}")
    print(f"  [FAIL] Python {sys.version_info.major}.{sys.version_info.minor}")
else:
    print(f"  [OK] Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

# Test 2: Tkinter (GUI)
print("\n[2/7] Testing tkinter (GUI)...")
try:
    import tkinter
    print("  [OK] tkinter available")
except ImportError:
    errors.append("tkinter not available")
    print("  [FAIL] tkinter not available")

# Test 3: Core file exists
print("\n[3/7] Testing core files...")
files_to_check = [
    'fame_desktop.py',
    'docker-compose.yml',
    'requirements_desktop.txt',
]

for file in files_to_check:
    if Path(file).exists():
        print(f"  [OK] {file} exists")
    else:
        errors.append(f"Missing file: {file}")
        print(f"  [FAIL] {file} not found")

# Test 4: Import fame_desktop
print("\n[4/7] Testing fame_desktop import...")
try:
    sys.path.insert(0, str(Path.cwd()))
    from fame_desktop import FAMEDesktopApp
    print("  [OK] fame_desktop imports successfully")
except ImportError as e:
    errors.append(f"Import error: {e}")
    print(f"  [FAIL] Cannot import fame_desktop - {e}")
except Exception as e:
    errors.append(f"Unexpected error: {e}")
    print(f"  [FAIL] Unexpected error - {e}")

# Test 5: Optional dependencies
print("\n[5/7] Testing optional dependencies...")
optional_deps = {
    'docker': 'Docker integration',
    'speech_recognition': 'Voice recognition',
    'pyttsx3': 'Text-to-speech',
    'matplotlib': 'Training visualization',
    'numpy': 'Numerical operations',
    'requests': 'HTTP requests',
}

for module, description in optional_deps.items():
    try:
        __import__(module)
        print(f"  [OK] {description} ({module})")
    except ImportError:
        warnings.append(f"Optional: {description} ({module}) not installed")
        print(f"  [OPTIONAL] {description} ({module}) not installed")

# Test 6: Training interface
print("\n[6/7] Testing Training Interface...")
try:
    sys.path.insert(0, str(Path('Training_Interface')))
    from training_gui import TrainingGUI
    print("  [OK] Training interface imports")
except ImportError:
    warnings.append("Training interface not importable")
    print("  [WARNING] Training interface import failed")

# Test 7: Voice interface
print("\n[7/7] Testing Voice Interface...")
try:
    sys.path.insert(0, str(Path('Voice_Interface')))
    from voice_app import VoiceInterface
    print("  [OK] Voice interface imports")
except ImportError:
    warnings.append("Voice interface not importable")
    print("  [WARNING] Voice interface import failed")

# Summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)

if errors:
    print(f"\n[ERRORS] ({len(errors)}):")
    for error in errors:
        print(f"   - {error}")
    print("\n[WARNING] These must be fixed before building .exe")
else:
    print("\n[OK] No critical errors!")

if warnings:
    print(f"\n[WARNINGS] ({len(warnings)}):")
    for warning in warnings:
        print(f"   - {warning}")
    print("\n[NOTE] These are optional features - app will work with limited functionality")

print("\n" + "=" * 60)

if errors:
    print("\n[FAIL] TEST FAILED - Fix errors before building .exe")
    sys.exit(1)
elif warnings:
    print("\n[WARNING] TEST PASSED WITH WARNINGS - .exe will work with limited features")
    sys.exit(0)
else:
    print("\n[OK] TEST PASSED - Ready to build .exe!")
    sys.exit(0)

