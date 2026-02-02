@echo off
:: Build script for Windows using PyInstaller

cd /d "%~dp0.."

:: Check if venv exists
if not exist .venv (
    echo Virtual environment not found. Please run run_app.bat first to set it up.
    pause
    exit /b
)

:: Activate venv
call .venv\Scripts\activate

:: Install PyInstaller if missing
pip install pyinstaller

:: Clean previous builds
rmdir /s /q build dist
del *.spec

:: Build Command
:: --onefile: Single executable
:: --windowed: No terminal window
:: --name: Executable name

pyinstaller --noconfirm --onefile --windowed --name "ThermalPlot" src\main.py

echo.
echo Build complete. Executable is in dist\ThermalPlot.exe
echo Don't forget to copy the 'config' folder next to the executable if you want to keep your settings!
pause
