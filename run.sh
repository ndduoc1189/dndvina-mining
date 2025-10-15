#!/bin/bash

# Mining Management Server Auto-Restart Script
# Tự động khởi động lại khi app bị crash

LOG_FILE="server.log"
PID_FILE="server.pid"
MAX_RESTARTS=100
RESTART_DELAY=5

echo "Starting Mining Management Server with auto-restart..."
echo "Log file: $LOG_FILE"
echo "PID file: $PID_FILE"
echo "Max restarts: $MAX_RESTARTS"
echo "Restart delay: $RESTART_DELAY seconds"
echo "Press Ctrl+C to stop"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping server..."
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            echo "Server stopped (PID: $PID)"
        fi
        rm -f "$PID_FILE"
    fi
    exit 0
}

# Trap signals to cleanup
trap cleanup SIGINT SIGTERM

# Install dependencies if needed
if ! python3 -c "import flask, psutil, requests" 2>/dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

restart_count=0

while true; do
    echo "========================================="
    echo "Starting server attempt #$((restart_count + 1))"
    echo "Time: $(date)"
    echo "========================================="
    
    # Start the server and capture PID
    python3 app.py >> "$LOG_FILE" 2>&1 &
    SERVER_PID=$!
    echo $SERVER_PID > "$PID_FILE"
    
    echo "Server started with PID: $SERVER_PID"
    
    # Wait for the process to finish
    wait $SERVER_PID
    EXIT_CODE=$?
    
    echo ""
    echo "Server stopped with exit code: $EXIT_CODE"
    echo "Time: $(date)"
    
    # Remove PID file
    rm -f "$PID_FILE"
    
    # Increment restart counter
    restart_count=$((restart_count + 1))
    
    # Check if we've reached max restarts
    if [ $restart_count -ge $MAX_RESTARTS ]; then
        echo "ERROR: Reached maximum restart limit ($MAX_RESTARTS)"
        echo "Please check the logs and fix the issue"
        exit 1
    fi
    
    # Check exit code
    if [ $EXIT_CODE -eq 0 ]; then
        echo "Server exited cleanly (exit code 0)"
        echo "This might be intentional shutdown"
        break
    else
        echo "Server crashed with exit code: $EXIT_CODE"
        echo "Restarting in $RESTART_DELAY seconds..."
        echo "Restart count: $restart_count/$MAX_RESTARTS"
        
        # Wait before restart
        sleep $RESTART_DELAY
    fi
done

echo "Script finished"