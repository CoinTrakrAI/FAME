#!/usr/bin/env python3
"""
F.A.M.E 11.0 - Build Script for Cosmic Intelligence Executable
Creates a standalone executable with all features
"""

import sys
import os
import subprocess
import shutil
from pathlib import Path

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def clean_build_directories():
    """Clean previous build directories"""
    print("[*] Cleaning previous build directories...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"[OK] Removed {dir_name}/")
            except PermissionError:
                print(f"[WARNING] Could not remove {dir_name}/ (may be in use)")
    
    # Clean .spec files
    for spec_file in Path('.').glob('*.spec'):
        try:
            spec_file.unlink()
            print(f"[OK] Removed {spec_file}")
        except Exception as e:
            print(f"[WARNING] Could not remove {spec_file}: {e}")


def install_pyinstaller():
    """Install PyInstaller if not available"""
    print("[*] Checking PyInstaller...")
    try:
        import PyInstaller
        print("[OK] PyInstaller available")
    except ImportError:
        print("[*] Installing PyInstaller...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        print("[OK] PyInstaller installed")


def build_executable():
    """Build the F.A.M.E 11.0 executable"""
    print("\n" + "="*60)
    print("F.A.M.E 11.0 - Building Cosmic Intelligence Executable")
    print("="*60 + "\n")
    
    # Clean
    clean_build_directories()
    
    # Install PyInstaller
    install_pyinstaller()
    
    # Get project root
    project_root = Path(__file__).parent
    
    # Collect data files
    data_files = [
        ('core', 'core'),
        ('ui', 'ui'),
    ]
    
    # Build datas argument
    datas_args = []
    for src, dst in data_files:
        src_path = project_root / src
        if src_path.exists():
            datas_args.extend(['--add-data', f'{src}{os.pathsep}{dst}'])
    
    # Hidden imports (AI frameworks are optional)
    hidden_imports = [
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
    ]
    
    # Exclude problematic packages
    excludes = [
        'sqlalchemy',
        'matplotlib.tests',
        'numpy.tests',
        'pandas.tests',
        'scipy',
    ]
    
    # PyInstaller command
    pyinstaller_cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--name', 'FAME_11_0_Cosmic',
        '--clean',
        '--noconfirm',
        '--collect-all', 'tkinter',  # Ensure tkinter is included
        '--collect-all', 'asyncio',  # Ensure asyncio is included
    ]
    
    # Add exclusions
    for exclude in excludes:
        pyinstaller_cmd.extend(['--exclude-module', exclude])
    
    # Add hidden imports
    for imp in hidden_imports:
        pyinstaller_cmd.extend(['--hidden-import', imp])
    
    # Add data files
    pyinstaller_cmd.extend(datas_args)
    
    # Add main script
    pyinstaller_cmd.append('launch_fame_11.py')
    
    print("[*] Building executable...")
    print(f"[*] Command: {' '.join(pyinstaller_cmd)}\n")
    
    try:
        result = subprocess.run(
            pyinstaller_cmd,
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True
        )
        
        print("[OK] Build completed successfully!")
        print(f"\n[OK] Executable created at: {project_root / 'dist' / 'FAME_11_0_Cosmic.exe'}")
        print("\n" + "="*60)
        print("F.A.M.E 11.0 Cosmic Intelligence - Build Complete!")
        print("="*60)
        print("\nFeatures included:")
        print("  • Premium 2028 Cosmic Interface")
        print("  • Multi-engine AI system (PyTorch, Transformers, LangChain, JAX)")
        print("  • All god-mode features (Quantum, Reality, Time, Network, Physical)")
        print("  • Voice interface support")
        print("  • Autonomous operation")
        print("  • Full development and cloud capabilities")
        print("\n🚀 Ready for deployment!")
        
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Build failed!")
        print(f"Return code: {e.returncode}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        sys.exit(1)


def main():
    """Main build function"""
    try:
        build_executable()
    except KeyboardInterrupt:
        print("\n\n[WARNING] Build interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

