@echo off
title VSC Industries ERP - Server Launcher
color 0B

echo =====================================================================
echo           VSC INDUSTRIES - ENTERPRISE ERP SYSTEM
echo   Client: VSC Industries (Vivek Singh Chauhan)
echo   Technical Lead: Rudraksh Saurabh Asthana (+91 8401113696)
echo =====================================================================
echo.

:: 1. Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not found in system PATH!
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo and ensure "Add Python to PATH" is checked during setup.
    echo.
    pause
    exit /b 1
)

echo [1/4] Python detected successfully.

:: 2. Check or create virtual environment
if not exist ".venv" (
    echo [2/4] Initializing local environment (.venv)...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo [3/4] Installing dependencies from requirements.txt...
    python -m pip install --upgrade pip >nul 2>nul
    pip install -r requirements.txt
) else (
    echo [2/4] Local environment detected (.venv).
    call .venv\Scripts\activate.bat
    echo [3/4] Verifying dependencies...
    pip install -r requirements.txt >nul 2>nul
)

:: 3. Launch browser in background after 2 seconds
echo [4/4] Starting VSC Industries ERP on http://127.0.0.1:8080 ...
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8080"

echo.
echo =====================================================================
echo   SERVER RUNNING: http://127.0.0.1:8080
echo   Press Ctrl+C to stop the server when finished.
echo =====================================================================
echo.

uvicorn app.main:app --host 127.0.0.1 --port 8080

pause
