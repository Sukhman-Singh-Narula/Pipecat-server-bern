#!/bin/bash

# Simple WebRTC AI Assistant - Quick Start Script

echo "🚀 Simple WebRTC AI Assistant Server"
echo "===================================="

# Check if .env exists
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "⚠️  .env file not found. Copying from .env.example..."
        cp .env.example .env
        echo "📝 Please edit .env file with your API keys:"
        echo "   - OPENAI_API_KEY"
        echo "   - DEEPGRAM_API_KEY" 
        echo "   - CARTESIA_API_KEY"
        echo ""
        read -p "Press Enter after editing .env file..."
    else
        echo "❌ No .env file found. Please create one with your API keys."
        exit 1
    fi
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "🔄 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing dependencies..."
pip install -r simple_requirements.txt

echo "✅ Starting server..."
echo "📖 Test client: file://$(pwd)/simple_test_client.html"
echo "🌐 Server URL: http://localhost:8000"
echo "🛑 Press Ctrl+C to stop"
echo ""

python simple_webrtc_server.py
