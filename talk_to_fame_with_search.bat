@echo off
REM Start FAME with SerpAPI keys configured
set SERPAPI_KEY=90f8748cb8ab624df5d503e1765e929491c57ef0b4d681fbe046f1febe045dbc
set SERPAPI_KEY_BACKUP=912dc3fe069c587aa89dc662a492998ded20a25dfc49f9961ff5e5c99168eeb1

cd /d "%~dp0"
python fame_simple.py

