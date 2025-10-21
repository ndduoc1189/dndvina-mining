#!/bin/bash

# Quick start script - can be run from anywhere
# Usage: bash /path/to/dndvina-mining/start.sh

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to script directory
cd "$SCRIPT_DIR" || {
    echo "❌ Error: Cannot change to directory $SCRIPT_DIR"
    exit 1
}

echo "============================================================"
echo "🚀 Mining Management Server - Quick Start"
echo "============================================================"
echo "📁 Working Directory: $SCRIPT_DIR"
echo ""

# Check if app.py exists
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found in $SCRIPT_DIR"
    exit 1
fi

# Check if config.py exists
if [ ! -f "config.py" ]; then
    echo "❌ Error: config.py not found in $SCRIPT_DIR"
    exit 1
fi

# Check for venv
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Check dependencies
if ! python3 -c "import flask, psutil, requests" 2>/dev/null; then
    echo "❌ Error: Missing dependencies"
    echo "Run: pip3 install -r requirements.txt"
    exit 1
fi

# Start server
echo "✅ Starting server..."
echo ""
python3 app.py
