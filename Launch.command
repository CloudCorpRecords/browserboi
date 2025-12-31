#!/bin/bash

# Unified Browser Agent Launcher
# This script handles both the background server and the Electron application.

cd "$(dirname "$0")"

echo "========================================"
echo "🚀 UNIFIED BROWSER AGENT LAUNCHER"
echo "========================================"
echo ""

# 1. Check for Virtual Environment
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Setting up..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r browser_agent/requirements.txt
else
    source venv/bin/activate
fi

# 2. Check for node_modules in launcher
if [ ! -d "launcher/node_modules" ]; then
    echo "📦 Initializing launcher dependencies..."
    cd launcher && npm install && cd ..
fi

echo "✅ Environment Ready"
echo "🌐 Starting Application..."
echo "----------------------------------------"

# 3. Launch the App
# This will spawn the Electron app, which in turn starts the Python server.
# Using 'open' on Mac to launch the .app if it exists, otherwise use npm start.

if [ -d "dist/mac-arm64/Browser Agent.app" ]; then
    open "dist/mac-arm64/Browser Agent.app"
    echo "📱 Launched Mac Application"
else
    echo "⚙️  Starting in Developer Mode..."
    cd launcher && npm start &
fi

echo ""
echo "📝 MONITORING LOGS (Press Ctrl+C to exit)"
echo "----------------------------------------"

# Keep the script running to see logs if in dev mode
wait
