#!/bin/bash
# Setup script for Video Downloader Bot

echo "=========================================="
echo "Video Downloader Bot - Setup Script"
echo "=========================================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Check if FFmpeg is installed
if command -v ffmpeg &> /dev/null; then
    echo "FFmpeg: Installed"
else
    echo "FFmpeg: NOT FOUND - Installing..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y ffmpeg
    elif command -v brew &> /dev/null; then
        brew install ffmpeg
    else
        echo "Please install FFmpeg manually: https://ffmpeg.org/download.html"
        exit 1
    fi
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Create directories
echo "Creating directories..."
mkdir -p downloads logs

# Copy .env.example if .env doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please edit .env file with your credentials!"
fi

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your BOT_TOKEN and ADMIN_IDS"
echo "2. Run the bot: python bot.py"
echo ""
