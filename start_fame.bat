@echo off
REM FAME Production Quick Start Script
echo ========================================
echo FAME - Production AI Assistant
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import asyncio" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements_production.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo Starting FAME Unified System...
echo.

REM Start FAME
python fame_unified.py

if errorlevel 1 (
    echo.
    echo ERROR: FAME failed to start
    pause
    exit /b 1
)

pause

