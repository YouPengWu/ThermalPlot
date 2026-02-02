#!/bin/bash

# Ensure we are in the project root
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install PyQt6 matplotlib

echo "Installation complete."
echo "To run the application:"
echo "  source .venv/bin/activate"
echo "  python src/main.py"
echo ""
echo "Or use the run_app.sh script."
