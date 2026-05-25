#!/bin/bash
# Web3 Job Hunter Bot — Quick Setup Script

echo "🚀 Web3 Job Hunter Bot Setup"
echo "============================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Install it from https://python.org"
    exit 1
fi

echo "✅ Python3 found: $(python3 --version)"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt --quiet

# Create .env if not exists
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  .env file created from template."
    echo "👉 Open .env and fill in:"
    echo "   BOT_TOKEN = your Telegram bot token"
    echo "   CHAT_ID   = your Telegram chat ID"
    echo ""
    echo "Then run this script again to start the bot."
    exit 0
fi

# Check if token is filled in
if grep -q "your_telegram_bot_token_here" .env; then
    echo "⚠️  Please fill in your BOT_TOKEN in the .env file first!"
    exit 1
fi

# Create data and logs dirs
mkdir -p data logs

echo ""
echo "✅ All good! Starting bot..."
echo "Press Ctrl+C to stop."
echo ""

python3 main.py
