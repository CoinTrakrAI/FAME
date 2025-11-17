#!/usr/bin/env python3
"""
F.A.M.E. Fixed Build Script - Python 3.13 Compatibility
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check Python version and warn about 3.13 issues"""
    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor == 13:
        print("[INFO] Python 3.13 detected - using PyInstaller 6.15+ and SQLAlchemy 2.0.23 compatibility mode")
        print("[OK] Python 3.13 supported!")
        return True
    elif version.major == 3 and version.minor in [11, 12]:
        print("[OK] Python version compatible!")
        return True
    else:
        print("[WARNING] Unknown Python version - proceeding with caution")
        return True

def install_compatible_versions():
    """Install versions known to work with PyInstaller"""
    version = sys.version_info
    if version.major == 3 and version.minor == 13:
        # Python 3.13 needs newer versions
        compatible_packages = {
            'sqlalchemy': '2.0.23',
            'pyinstaller': '>=6.10.0',  # Python 3.13 compatible
            'cryptography': '41.0.7',
            'setuptools': '68.2.2'
        }
    else:
        # Python 3.11/3.12 compatibility
        compatible_packages = {
            'sqlalchemy': '2.0.23',
            'pyinstaller': '5.13.2',
            'cryptography': '41.0.7',
            'setuptools': '68.2.2'
        }
    
    print("[*] Installing compatible package versions...")
    for package, version in compatible_packages.items():
        try:
            if '>=' in version or '~=' in version:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', f'{package}{version}'], 
                                    stdout=sys.stdout, stderr=sys.stderr)
                print(f"[OK] {package}{version} installed")
            else:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', f'{package}=={version}'], 
                                    stdout=sys.stdout, stderr=sys.stderr)
                print(f"[OK] {package}=={version} installed")
        except subprocess.CalledProcessError as e:
            print(f"[WARNING] Failed to install {package}, trying latest...")
            print(f"Error: {e}")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', package],
                                    stdout=sys.stdout, stderr=sys.stderr)
                print(f"[OK] {package} (latest) installed as fallback")
            except Exception as e2:
                print(f"[ERROR] Could not install {package}: {e2}")

def create_pyinstaller_spec():
    """Create a custom .spec file to handle SQLAlchemy issues"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['launch_fame_11.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('core', 'core'),
        ('ui', 'ui'),
    ],
    hiddenimports=[
        'core',
        'core.ai_engine_manager',
        'core.quantum_dominance',
        'core.reality_manipulator',
        'core.time_manipulator',
        'core.network_god',
        'core.physical_god',
        'core.consciousness_engine',
        'core.universal_developer',
        'core.cloud_master',
        'core.evolution_engine',
        'core.autonomous_investor',
        'core.docker_manager',
        'ui',
        'ui.cosmic_interface',
        'ui.advanced_voice',
        'ui.cosmic_styles',
        'asyncio',
        'json',
        'threading',
        'datetime',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'sqlalchemy',  # Exclude if causing issues
        'matplotlib.tests',
        'numpy.tests',
        'pandas.tests',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

a.pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    a.pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FAME_11_0_Cosmic',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    
    with open('fame_build.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("[OK] Created custom PyInstaller spec file")

def build_with_workarounds():
    """Build with compatibility workarounds"""
    print("[*] Building F.A.M.E. with compatibility fixes...")
    
    # Use existing spec file instead of creating new one
    spec_file = Path(__file__).parent / 'FAME_11_0_Cosmic.spec'
    if not spec_file.exists():
        print("[*] Creating custom spec file...")
        create_pyinstaller_spec()
        spec_file = Path(__file__).parent / 'fame_build.spec'
    
    # Set environment variables to help with compatibility
    env = os.environ.copy()
    env['PYTHONHASHSEED'] = '0'
    
    try:
        # Build using the spec file
        result = subprocess.run([
            sys.executable, '-m', 'PyInstaller',
            str(spec_file),
            '--clean',
            '--noconfirm'
        ], env=env, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            exe_path = Path(__file__).parent / 'dist' / 'FAME_11_0_Cosmic.exe'
            if exe_path.exists():
                print("[OK] Build successful!")
                print(f"[OK] Executable location: {exe_path}")
                return True
            else:
                print("[ERROR] Build completed but executable not found")
                return False
        else:
            print("[ERROR] Build failed!")
            return False
            
    except Exception as e:
        print(f"[ERROR] Build error: {e}")
        return False

def main():
    """Main build process with fixes"""
    print("=" * 60)
    print("F.A.M.E. BUILD FIX - Python 3.13 Compatibility")
    print("=" * 60)
    
    # Check Python version
    compatible = check_python_version()
    if not compatible:
        print("[WARNING] Compatibility issues detected, but proceeding with build...")
    
    # Install compatible versions
    install_compatible_versions()
    
    # Try building with workarounds
    success = build_with_workarounds()
    
    if success:
        print("\n" + "=" * 60)
        print("BUILD COMPLETE!")
        print("=" * 60)
        print("\nExecutable created: dist/FAME_11_0_Cosmic.exe")
    else:
        print("\n" + "=" * 60)
        print("BUILD FAILED - Alternative Options:")
        print("=" * 60)
        print("1. Use Python 3.11 virtual environment")
        print("2. Try manual build: python -m PyInstaller fame_build.spec")
        print("3. Check error messages above for specific issues")

if __name__ == "__main__":
    main()


