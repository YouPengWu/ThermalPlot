#!/bin/bash
# Build script for Linux using PyInstaller

# Ensure we are in the project root
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

# Check if venv exists and activate
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Virtual environment not found. Please run install.sh first."
    exit 1
fi

# Install PyInstaller if missing
pip install pyinstaller

# Clean previous builds
rm -rf build dist *.spec

# Build Command
# --onefile: Single executable
# --windowed: No terminal window
# --name: Executable name
# --add-data: Include config folder (optional, but good for defaults)
# Note: config.json is better kept external for user editing, so we might NOT bundle it inside the onefile, 
# but we should ensure the app looks for it in the same dir. 
# The code currently looks in os.getcwd()/config, so it should work if config folder is next to exe.

pyinstaller --noconfirm --onefile --windowed --name "ThermalPlot" src/main.py

echo "Build complete. Executable is in dist/ThermalPlot"
echo "Don't forget to copy the 'config' folder next to the executable if you want to keep your settings!"
