#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to script directory
cd "$SCRIPT_DIR" || {
    echo "❌ Error: Cannot change to directory $SCRIPT_DIR"
    exit 1
}

echo "============================================================"
echo "🚀 Mining Management Server - Auto-Restart"
echo "============================================================"
echo "📁 Working Directory: $SCRIPT_DIR"
echo "Press Ctrl+C to stop"
echo ""

# Update code from git repository
echo "Updating code from git repository..."
if git pull 2>/dev/null; then
    echo "✅ Code updated successfully"
else
    echo "⚠️  Git pull skipped (not a git repo or no changes)"
fi
echo ""

# Install dependencies if needed
if ! python3 -c "import flask, psutil, requests" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip3 install -r requirements.txt
    echo ""
fi

# Check if app.py exists
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found in $SCRIPT_DIR"
    exit 1
fi

echo "✅ Starting server from: $SCRIPT_DIR/app.py"
echo ""

# Trap SIGINT (Ctrl+C) for clean shutdown
trap 'echo ""; echo "🛑 Received Ctrl+C, stopping server..."; exit 0' INT

# Simple auto-restart loop
while true; do
    echo "========================================="
    echo "Starting server at $(date)"
    echo "========================================="
    
    # Run the server and show output directly
    python3 app.py
    
    EXIT_CODE=$?
    echo ""
    echo "Server stopped with exit code: $EXIT_CODE at $(date)"
    
    # If exit code is 0 or 130 (Ctrl+C), it was intentional shutdown
    if [ $EXIT_CODE -eq 0 ] || [ $EXIT_CODE -eq 130 ]; then
        echo "Clean shutdown detected. Exiting."
        break
    fi
    
    # Otherwise, restart after 3 seconds
    echo "Restarting in 3 seconds..."
    sleep 3
done

echo "Script finished"