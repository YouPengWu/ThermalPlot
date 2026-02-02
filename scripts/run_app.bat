@echo off
cd /d "%~dp0.."

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Installing dependencies...
pip install PyQt6 matplotlib

echo Starting Application...
python src\main.py

pause
