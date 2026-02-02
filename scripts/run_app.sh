#!/bin/bash

# Get directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

# Check for venv
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Please run install.sh first."
    exit 1
fi

# Activate and run
source .venv/bin/activate
python src/main.py
