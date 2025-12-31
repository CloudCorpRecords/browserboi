#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

echo "========================================"
echo "   Starting Browser AI Agent..."
echo "========================================"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "[!] Virtual environment not found. Setting up..."
    python3 -m venv venv
    source venv/bin/activate
    echo "[*] Installing dependencies..."
    pip install -r browser_agent/requirements.txt
    echo "[*] Installing Playwright browsers..."
    playwright install
    echo "[+] Setup complete."
else
    source venv/bin/activate
fi

# Function to open browser
open_browser() {
    sleep 2
    echo "[*] Opening Dashboard..."
    open "http://localhost:8000"
}

open_browser &

echo "[*] Starting Server on Port 8000..."
uvicorn browser_agent.server.main:app --host 0.0.0.0 --port 8000
