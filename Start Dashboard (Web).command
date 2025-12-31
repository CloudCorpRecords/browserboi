#!/bin/bash

# Browser Agent Launcher
# Double-click this file to start the Browser Agent

cd "$(dirname "$0")"

echo "🚀 Starting Browser Agent..."
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "✅ Environment ready"
echo "🌐 Starting server on http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "----------------------------------------"
echo ""

# Start the server
python3 -m uvicorn browser_agent.server.main:app --host 0.0.0.0 --port 8000

# Keep terminal open on exit
echo ""
echo "Server stopped. You can close this window."
read -p "Press Enter to exit..."
