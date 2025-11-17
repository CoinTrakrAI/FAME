@echo off
echo Installing F.A.M.E 6.0 Desktop Application...
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed. Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo [1/6] Python found
python --version

:: Create virtual environment
echo.
echo [2/6] Creating virtual environment...
if exist "fame_env" (
    echo Virtual environment already exists. Skipping...
) else (
    python -m venv fame_env
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

:: Activate virtual environment
call fame_env\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

:: Upgrade pip
echo.
echo [3/6] Upgrading pip...
python -m pip install --upgrade pip

:: Install dependencies
echo.
echo [4/6] Installing dependencies...
pip install -r requirements_desktop.txt
if errorlevel 1 (
    echo WARNING: Some dependencies may have failed to install
    echo You can try installing them individually
)

:: Check Docker
echo.
echo [5/6] Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Docker is not installed. 
    echo Please install Docker Desktop from docker.com for full functionality
    echo The application will work with limited features.
) else (
    echo Docker found:
    docker --version
)

:: Create desktop shortcut
echo.
echo [6/6] Creating desktop shortcut...
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\create_shortcut.vbs"
echo sLinkFile = "%userprofile%\Desktop\FAME_Launcher.lnk" >> "%TEMP%\create_shortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\create_shortcut.vbs"
echo oLink.TargetPath = "%~dp0fame_env\Scripts\pythonw.exe" >> "%TEMP%\create_shortcut.vbs"
echo oLink.Arguments = "%~dp0fame_desktop.py" >> "%TEMP%\create_shortcut.vbs"
echo oLink.WorkingDirectory = "%~dp0" >> "%TEMP%\create_shortcut.vbs"
echo oLink.Description = "F.A.M.E 6.0 Living AI System" >> "%TEMP%\create_shortcut.vbs"
echo oLink.IconLocation = "%~dp0fame_env\Scripts\pythonw.exe,0" >> "%TEMP%\create_shortcut.vbs"
echo oLink.Save >> "%TEMP%\create_shortcut.vbs"
cscript //nologo "%TEMP%\create_shortcut.vbs" >nul 2>&1
del "%TEMP%\create_shortcut.vbs" >nul 2>&1

echo.
echo ================================================================
echo    ✅ F.A.M.E 6.0 Installation Complete!
echo ================================================================
echo.
echo 🚀 To start the application:
echo    1. Double-click "FAME_Launcher" on your desktop
echo    2. Or run: python fame_desktop.py
echo    3. Or activate venv and run: fame_env\Scripts\activate && python fame_desktop.py
echo.
echo 🐳 Make sure Docker Desktop is running for full functionality
echo.
echo 📝 Note: First launch may take a few seconds to initialize
echo.
pause

