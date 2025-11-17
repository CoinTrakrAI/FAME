@echo off
REM F.A.M.E 6.0 Desktop - Executable Builder
REM This script builds FAME_Launcher.exe from fame_desktop.py

echo ================================================================
echo    F.A.M.E 6.0 Desktop - Executable Builder
echo ================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo [1/5] Python found:
python --version
echo.

REM Check if virtual environment exists
if exist "fame_env\Scripts\activate.bat" (
    echo [2/5] Activating virtual environment...
    call fame_env\Scripts\activate.bat
) else (
    echo [2/5] Virtual environment not found. Creating...
    python -m venv fame_env
    call fame_env\Scripts\activate.bat
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo.
echo [3/5] Checking PyInstaller installation...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

echo.
echo [4/5] Building executable with PyInstaller...
echo This may take several minutes...
echo.

python -m PyInstaller build_exe.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo.
    echo Common issues:
    echo   - Missing dependencies: Run install_fame.bat first
    echo   - PyInstaller not installed: pip install pyinstaller
    echo   - Path issues: Make sure you're in the FAME_Desktop directory
    echo.
    pause
    exit /b 1
)

echo.
echo [5/5] Build complete!
echo.
echo ================================================================
echo    SUCCESS: Executable created!
echo ================================================================
echo.
echo File location: dist\FAME_Launcher.exe
echo.
echo You can now:
echo   1. Run dist\FAME_Launcher.exe to test
echo   2. Copy it anywhere to distribute
echo   3. Create a shortcut on your desktop
echo.
echo NOTE: The .exe includes all dependencies but requires:
echo   - Docker Desktop (for LocalAI features)
echo   - Microphone (for voice features)
echo   - Internet connection (for API calls)
echo.
pause

