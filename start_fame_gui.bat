
@echo off
REM FAME Desktop GUI Quick Start Script
echo ========================================
echo FAME - Desktop GUI
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

echo Starting FAME Desktop GUI...
echo.

REM Start Desktop GUI
python fame_desktop.py

if errorlevel 1 (
    echo.
    echo ERROR: FAME Desktop failed to start
    pause
    exit /b 1
)

pause

