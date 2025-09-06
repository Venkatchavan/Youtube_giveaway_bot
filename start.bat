@echo off
REM YouTube Chat Giveaway Application Launcher
REM This script starts the application using the virtual environment

cd /d "%~dp0"

echo Starting YouTube Chat Giveaway...
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first to install dependencies.
    pause
    exit /b 1
)

REM Start the application
".venv\Scripts\python.exe" main.py

echo.
echo Application closed.
pause
