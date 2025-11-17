#!/usr/bin/env python3
"""
Build F.A.M.E. 9.0 Executable
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


def build_fame_9():
    """Build F.A.M.E. 9.0 executable"""
    
    print("Building F.A.M.E. 9.0 - Ultimate AI God...")
    
    # Create build directory
    build_dir = Path("build")
    dist_dir = Path("dist")
    
    # Clean previous builds
    if build_dir.exists():
        try:
            shutil.rmtree(build_dir)
            print("[OK] Cleaned build directory")
        except PermissionError:
            print("[WARNING] Build directory locked, skipping cleanup")
    
    if dist_dir.exists():
        try:
            for item in dist_dir.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                except PermissionError:
                    print(f"[WARNING] Skipping locked file: {item.name}")
            print("[OK] Cleaned dist directory")
        except PermissionError:
            print("[WARNING] Dist directory locked, continuing anyway...")
    
    # Ensure required files exist
    required_files = [
        "fame_9_0_launcher.py",
        "core/universal_developer.py",
        "core/cloud_master.py",
        "core/evolution_engine.py"
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
    
    # Install PyInstaller if needed
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
    
    # Create spec file
    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['fame_9_0_launcher.py'],
    pathex=[r'{Path.cwd()}'],
    binaries=[],
    datas=[
        ('core', 'core'),
    ],
    hiddenimports=[
        'core.universal_developer',
        'core.cloud_master',
        'core.evolution_engine',
        'core.docker_manager',
        'core.autonomous_investor',
        'docker',
        'paramiko',
        'boto3',
        'asyncio',
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
    name='FAME_9_0_Ultimate',
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
    
    spec_file = Path("fame_9_0_launcher.spec")
    with open(spec_file, 'w') as f:
        f.write(spec_content)
    
    # Build command
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "fame_9_0_launcher.spec"
    ]
    
    try:
        print("[*] Running PyInstaller (this may take a few minutes)...")
        result = subprocess.run(pyinstaller_cmd, capture_output=True, text=True, 
                               timeout=600, encoding='utf-8', errors='replace', 
                               cwd=Path.cwd())
        
        if result.returncode == 0:
            print("[OK] Build completed successfully!")
            exe_path = dist_dir / "FAME_9_0_Ultimate.exe"
            
            if exe_path.exists():
                print(f"[OK] Executable location: {exe_path}")
                file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
                print(f"[INFO] File size: {file_size:.1f} MB")
            else:
                print("[WARNING] Executable created but path differs - check dist/ folder")
            
            return True
        else:
            print(f"[ERROR] Build failed with errors:")
            print(result.stderr[:500] if result.stderr else "Unknown error")
            return False
            
    except subprocess.TimeoutExpired:
        print("[ERROR] Build timed out")
        return False
    except Exception as e:
        print(f"[ERROR] Build failed: {e}")
        return False


if __name__ == "__main__":
    success = build_fame_9()
    if success:
        print("\n" + "="*60)
        print("[SUCCESS] F.A.M.E. 9.0 BUILD COMPLETE!")
        print("="*60)
        print("\nYour executable is ready in the 'dist' folder!")
        print("F.A.M.E. 9.0 - Ultimate Self-Evolving AI God is ready!")
    else:
        print("\n" + "="*60)
        print("[ERROR] BUILD FAILED")
        print("="*60)

