@echo off
REM Set SerpAPI Keys for FAME
REM This sets environment variables for the current session

set SERPAPI_KEY=90f8748cb8ab624df5d503e1765e929491c57ef0b4d681fbe046f1febe045dbc
set SERPAPI_KEY_BACKUP=912dc3fe069c587aa89dc662a492998ded20a25dfc49f9961ff5e5c99168eeb1

echo API keys set for this session
echo Starting FAME...
echo.

cd /d "%~dp0"
python fame_simple.py

