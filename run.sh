#!/bin/bash
# Quick start script for AI Coder

cd "$(dirname "$0")"

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Install: apt install python3"
    exit 1
fi

echo "🚀 AI Coder Launcher"
echo ""

# Install dependencies if needed
if ! python3 -c "import openai" 2>/dev/null; then
    echo "📦 First run - installing dependencies..."
    python3 install.py
fi

# Start AI Coder
echo "🤖 Starting AI Coder..."
echo ""
python3 ai_coder.py "$@"
