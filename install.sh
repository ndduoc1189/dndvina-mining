#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to script directory
cd "$SCRIPT_DIR" || {
    echo "❌ Error: Cannot change to directory $SCRIPT_DIR"
    exit 1
}

# Install script for Ubuntu/Debian systems

echo "==============================================="
echo "Mining Management Server - Ubuntu Installation"
echo "==============================================="
echo "📁 Installation Directory: $SCRIPT_DIR"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  WARNING: Running as root. Consider using a regular user."
fi

# Update system
echo "Updating system packages..."
sudo apt update

# Install Python3 and pip if not installed
echo "Installing Python3 and pip..."
sudo apt install -y python3 python3-pip python3-venv

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y curl wget git

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Make scripts executable
echo "Making scripts executable..."
chmod +x run.sh
chmod +x install.sh

# Create systemd service (optional)
read -p "Do you want to create a systemd service for auto-start? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    SERVICE_FILE="/etc/systemd/system/mining-manager.service"
    WORK_DIR="$SCRIPT_DIR"
    USER=$(whoami)
    
    echo "Creating systemd service..."
    sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Mining Management Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORK_DIR
Environment=PATH=$WORK_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$WORK_DIR/venv/bin/python $WORK_DIR/app.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable mining-manager.service
    
    echo ""
    echo "✅ Service created! Control commands:"
    echo "  sudo systemctl start mining-manager"
    echo "  sudo systemctl stop mining-manager"
    echo "  sudo systemctl status mining-manager"
    echo "  sudo systemctl restart mining-manager"
    echo "  sudo journalctl -u mining-manager -f"
fi

echo ""
echo "==============================================="
echo "✅ Installation completed!"
echo "==============================================="
echo ""
echo "📂 Installation Path: $SCRIPT_DIR"
echo ""
echo "To start manually:"
echo "  cd $SCRIPT_DIR"
echo "  source venv/bin/activate"
echo "  ./run.sh"
echo ""
echo "Or without venv (system Python):"
echo "  cd $SCRIPT_DIR"
echo "  ./run.sh"
echo ""
echo "To start with systemd (if created):"
echo "  sudo systemctl start mining-manager"
echo ""
echo "Server will run on: http://0.0.0.0:9098"
echo "API documentation: Check README.md"
echo ""