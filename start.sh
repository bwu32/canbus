#!/bin/bash

# CAN Bus Security Simulation - Quick Start Script

echo "🚗 CAN Bus Security Simulation Setup"
echo "====================================="
echo ""

# Check Python version
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Found Python $PYTHON_VERSION"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt --quiet

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed"
echo ""

# Start the simulation
echo "🚀 Starting CAN Bus Simulation Server..."
echo ""
echo "Server will start on ws://localhost:8765"
echo ""
echo "📋 Next steps:"
echo "1. Server will start in 3 seconds"
echo "2. Open the frontend in your browser (Claude.ai artifacts or local React)"
echo "3. Start experimenting with security measures and attacks!"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

sleep 3

# Run the server
python3 server.py