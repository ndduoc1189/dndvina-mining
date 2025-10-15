#!/bin/bash

# Install script for Ubuntu/Debian systems

echo "==============================================="
echo "Mining Management Server - Ubuntu Installation"
echo "==============================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "WARNING: Running as root. Consider using a regular user."
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
    WORK_DIR=$(pwd)
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
Environment=PATH=$WORK_DIR/venv/bin
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
    
    echo "Service created! You can control it with:"
    echo "  sudo systemctl start mining-manager"
    echo "  sudo systemctl stop mining-manager"
    echo "  sudo systemctl status mining-manager"
    echo "  sudo systemctl restart mining-manager"
fi

echo ""
echo "==============================================="
echo "Installation completed!"
echo "==============================================="
echo ""
echo "To start manually:"
echo "  source venv/bin/activate"
echo "  ./run.sh"
echo ""
echo "To start with systemd (if created):"
echo "  sudo systemctl start mining-manager"
echo ""
echo "Server will run on: http://localhost:5000"
echo "API documentation: Check README.md"
echo ""