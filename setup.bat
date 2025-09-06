@echo off
REM Setup script for YouTube Chat Giveaway Application
REM This script creates a virtual environment and installs dependencies

cd /d "%~dp0"

echo Setting up YouTube Chat Giveaway Application...
echo.

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment!
        echo Please ensure Python 3.8+ is installed and available in PATH.
        pause
        exit /b 1
    )
)

REM Activate virtual environment and install dependencies
echo Installing dependencies...
".venv\Scripts\pip.exe" install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo Setup completed successfully!
echo.
echo To start the application, run: start.bat
echo Or manually run: .venv\Scripts\python.exe main.py
echo.
pause
