#!/bin/bash

# Simple auto-restart script for Mining Management Server
echo "Starting Mining Management Server with auto-restart..."
echo "Press Ctrl+C to stop"
echo ""

# Update code from git repository
echo "Updating code from git repository..."
if git pull; then
    echo "✅ Code updated successfully"
else
    echo "⚠️  Git pull failed, continuing with current code"
fi
echo ""

# Install dependencies if needed
if ! python3 -c "import flask, psutil, requests" 2>/dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
    echo ""
fi

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
    
    # If exit code is 0, it was intentional shutdown
    if [ $EXIT_CODE -eq 0 ]; then
        echo "Clean shutdown detected. Exiting."
        break
    fi
    
    # Otherwise, restart after 3 seconds
    echo "Restarting in 3 seconds..."
    sleep 3
done

echo "Script finished"