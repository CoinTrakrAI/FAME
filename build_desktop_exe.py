#!/usr/bin/env python3
"""
Build FAME Desktop as .exe using PyInstaller
Creates a single executable file with all dependencies
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent


def check_dependencies():
    """Check if required tools are installed"""
    print("Checking dependencies...")
    
    # Check PyInstaller
    try:
        import PyInstaller
        print("✅ PyInstaller is installed")
    except ImportError:
        print("❌ PyInstaller is not installed")
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("✅ PyInstaller installed")
    
    # Check PyQt5
    try:
        import PyQt5
        print("✅ PyQt5 is installed")
    except ImportError:
        print("⚠️ PyQt5 is not installed (will use Tkinter fallback)")
    
    return True


def create_spec_file():
    """Create PyInstaller spec file"""
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['fame_desktop_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('core', 'core'),
        ('services', 'services'),
        ('ui', 'ui'),
        ('orchestrator', 'orchestrator'),
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'core.finance_first_router',
        'core.finance_first_responder',
        'core.living_system',
        'core.localai_manager',
        'core.assistant.assistant_api',
        'services.premium_price_service',
        'orchestrator.brain',
    ],
    hookspath=[],
    hooksconfig={},
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
    name='FAME_Desktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
)
"""
    
    spec_path = BASE_DIR / "fame_desktop.spec"
    with open(spec_path, 'w') as f:
        f.write(spec_content)
    
    print(f"✅ Created spec file: {spec_path}")
    return spec_path


def build_exe():
    """Build the executable"""
    print("\n" + "="*60)
    print("Building FAME Desktop Executable")
    print("="*60 + "\n")
    
    # Check dependencies
    check_dependencies()
    
    # Create spec file
    spec_file = create_spec_file()
    
    # Build command
    build_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file)
    ]
    
    print(f"Running: {' '.join(build_cmd)}\n")
    
    try:
        result = subprocess.run(build_cmd, check=True, cwd=BASE_DIR)
        print("\n" + "="*60)
        print("✅ Build successful!")
        print("="*60)
        print(f"\nExecutable location: {BASE_DIR / 'dist' / 'FAME_Desktop.exe'}")
        print("\nYou can now distribute FAME_Desktop.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed: {e}")
        return False


def create_installer_script():
    """Create a simple installer script"""
    installer_content = """@echo off
echo ========================================
echo FAME Desktop - Installer
echo ========================================
echo.

echo Checking for Docker Desktop...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker Desktop is not installed.
    echo.
    echo Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop/
    echo.
    echo After installing Docker Desktop, run this installer again.
    pause
    exit /b 1
)

echo Docker Desktop is installed.
echo.

echo Creating desktop shortcut...
set SCRIPT_DIR=%~dp0
set EXE_PATH=%SCRIPT_DIR%FAME_Desktop.exe
set SHORTCUT=%USERPROFILE%\\Desktop\\FAME Desktop.lnk

powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT%'); $Shortcut.TargetPath = '%EXE_PATH%'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.Save()"

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo FAME Desktop has been installed.
echo A shortcut has been created on your desktop.
echo.
echo To start LocalAI (required for local AI):
echo   1. Start Docker Desktop
echo   2. Run: docker run -d --name local-ai -p 8080:8080 localai/localai:latest
echo.
pause
"""
    
    installer_path = BASE_DIR / "install_fame_desktop.bat"
    with open(installer_path, 'w') as f:
        f.write(installer_content)
    
    print(f"✅ Created installer script: {installer_path}")
    return installer_path


def main():
    """Main build process"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║   FAME Desktop - Executable Builder                     ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Build executable
    if build_exe():
        # Create installer
        create_installer_script()
        
        print("\n" + "="*60)
        print("Build Process Complete!")
        print("="*60)
        print("\nNext steps:")
        print("1. Test FAME_Desktop.exe in the dist/ folder")
        print("2. Create a distribution package:")
        print("   - Copy FAME_Desktop.exe to a folder")
        print("   - Include install_fame_desktop.bat")
        print("   - Include Docker Desktop installer (optional)")
        print("   - Create a README with setup instructions")
        print("\n" + "="*60)
    else:
        print("\nBuild failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

