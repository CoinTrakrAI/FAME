#!/usr/bin/env python3
"""
F.A.M.E. 8.0 Build Script - Creates downloadable executable
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Fix Windows console encoding for Unicode
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def build_fame_executable():
    """Build the F.A.M.E. executable with all dependencies"""
    
    print("Building F.A.M.E. 8.0 God Mode Executable...")
    
    # Create build directory
    build_dir = Path("build")
    dist_dir = Path("dist")
    
    # Clean previous builds (skip if files are locked)
    if build_dir.exists():
        try:
            shutil.rmtree(build_dir)
            print("[OK] Cleaned build directory")
        except PermissionError:
            print("[WARNING] Build directory locked, skipping cleanup")
    
    if dist_dir.exists():
        try:
            # Try to remove individual files first
            for item in dist_dir.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                except PermissionError:
                    print(f"[WARNING] Skipping locked file: {item.name}")
            print("[OK] Cleaned dist directory (some files may be in use)")
        except PermissionError:
            print("[WARNING] Dist directory locked, continuing anyway...")
    
    # Ensure all required files exist
    required_files = [
        "fame_launcher.py",
        "core/docker_manager.py",
        "core/autonomous_investor.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"[ERROR] Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("[OK] All required files present")
    
    # Install PyInstaller if not present
    try:
        import PyInstaller
        print("[OK] PyInstaller found")
    except ImportError:
        print("[*] Installing PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"], 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("[OK] PyInstaller installed")
        except:
            print("[ERROR] Failed to install PyInstaller")
            return False
    
    # Install required dependencies
    dependencies = [
        "docker", "pandas", "numpy", "yfinance", "requests", "psutil", "aiohttp"
    ]
    
    print("[*] Checking dependencies...")
    for dep in dependencies:
        try:
            __import__(dep.replace('-', '_'))
        except ImportError:
            print(f"   Installing {dep}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except:
                print(f"   [WARNING] {dep} may not be installed correctly")
    
    # Build the executable
    print("[*] Creating executable...")
    
    # Create spec file for better control
    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['fame_launcher.py'],
    pathex=[r'{Path.cwd()}'],
    binaries=[],
    datas=[
        ('core', 'core'),
    ],
    hiddenimports=[
        'docker',
        'yfinance',
        'pandas',
        'numpy',
        'requests',
        'aiohttp',
        'psutil',
        'core.docker_manager',
        'core.autonomous_investor',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FAME_GodMode_v8.0',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
"""
    
    spec_file = Path("fame_launcher.spec")
    with open(spec_file, 'w') as f:
        f.write(spec_content)
    
    # Use python -m PyInstaller instead of direct command
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "fame_launcher.spec"
    ]
    
    try:
        print("   [*] Running PyInstaller (this may take a few minutes)...")
        print(f"   Command: {' '.join(pyinstaller_cmd)}")
        result = subprocess.run(pyinstaller_cmd, capture_output=True, text=True, timeout=600, encoding='utf-8', errors='replace', cwd=Path.cwd())
        
        if result.returncode == 0:
            print("[OK] Build completed successfully!")
            exe_path = dist_dir / "FAME_GodMode_v8.0.exe"
            
            if exe_path.exists():
                print(f"[OK] Executable location: {exe_path}")
                file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
                print(f"[INFO] File size: {file_size:.1f} MB")
            else:
                print("[WARNING] Executable created but path differs - check dist/ folder")
            
            # Create a simple README
            readme_content = """
# F.A.M.E. 8.0 - God Mode AI

## 🚀 Quick Start

1. Double-click `FAME_GodMode_v8.0.exe`

2. Ensure Docker Desktop is installed and running (optional but recommended)

3. Click "ACTIVATE F.A.M.E." 

4. The AI will automatically connect to the internet and begin learning

## 🔧 Requirements

- Windows 10/11
- Docker Desktop installed (for LocalAI features - optional)
- Internet connection
- 8GB+ RAM recommended

## 🧠 What F.A.M.E. Does

- Automatically connects to Docker and starts AI engine (if available)
- Begins learning financial markets immediately
- Analyzes stocks, crypto, and all major assets
- Develops advanced trading strategies
- Continuously self-improves 24/7

## 📊 Monitoring

The interface shows real-time:

- Internet connectivity status
- Docker status  
- AI learning progress
- Market analysis updates

The AI works autonomously once activated!

## 🎤 Voice Features

If you want voice interaction:

1. Install speech libraries:
   pip install speechrecognition pyttsx3
   
   For PyAudio (Windows):
   pip install pipwin
   pipwin install pyaudio
   
   OR download wheel from:
   https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

2. Voice features will automatically activate when libraries are installed

## 🆘 Troubleshooting

- **Docker not connecting**: Set DOCKER_HOST environment variable to: npipe:////./pipe/docker_engine
- **Voice not working**: Install required libraries (see above)
- **Financial data errors**: Ensure internet connection and install yfinance: pip install yfinance

For detailed setup, see DOCKER_SETUP_GUIDE.md
"""
            
            readme_path = dist_dir / "README.txt"
            with open(readme_path, "w", encoding='utf-8') as f:
                f.write(readme_content)
                
            print("[OK] README created with instructions")
            return True
        else:
            print(f"[ERROR] Build failed with errors:")
            print(result.stderr[:500])
            return False
            
    except subprocess.TimeoutExpired:
        print("[ERROR] Build timed out (took longer than 10 minutes)")
        return False
    except Exception as e:
        print(f"[ERROR] Build failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = build_fame_executable()
    if success:
        print("\n" + "="*60)
        print("[SUCCESS] BUILD COMPLETE!")
        print("="*60)
        print("\nYour executable is ready in the 'dist' folder!")
        print("Users can download and run it immediately.")
    else:
        print("\n" + "="*60)
        print("[ERROR] BUILD FAILED")
        print("="*60)
        print("\nCheck errors above and try again.")

