# Elite YouTube & Instagram Video Downloader Bot

A master-level Telegram bot for downloading videos from YouTube and Instagram with advanced features, multi-quality support, admin panel, and comprehensive statistics.

## Features

### YouTube Support
- Regular videos (all qualities from 144p to 4K)
- YouTube Shorts
- Live streams
- Audio-only extraction (MP3)
- Multiple quality selection (144p, 240p, 360p, 480p, 720p, 1080p, 1440p, 2160p, Best)

### Instagram Support
- Reels
- Video posts
- IGTV videos
- Stories (when available)
- Multiple download methods (yt-dlp, Instaloader, RapidAPI)

### Bot Features
- User database with SQLite
- Download statistics (personal & global)
- Admin panel with broadcast
- Rate limiting per user
- Progress tracking during download
- User settings (default quality, preferred format)
- Maintenance mode
- Ban/unban users
- Automatic file cleanup
- Comprehensive logging

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- FFmpeg (required for video/audio processing)

### Step 1: Install FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html and add to PATH

### Step 2: Clone and Setup

```bash
# Navigate to bot directory
cd telegram_video_bot

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Required configuration:
```
BOT_TOKEN=your_telegram_bot_token_here      # Get from @BotFather
ADMIN_IDS=your_telegram_user_id             # Your Telegram numeric ID
```

Optional configuration:
```
INSTAGRAM_USERNAME=your_instagram_username   # For private content
INSTAGRAM_PASSWORD=your_instagram_password
RAPIDAPI_KEY=your_rapidapi_key              # Instagram API fallback
```

### Step 4: Run the Bot

```bash
python bot.py
```

## Deployment

### Using PM2 (Recommended)

```bash
# Install PM2
npm install -g pm2

# Start bot with PM2
pm2 start bot.py --name video-downloader-bot --interpreter python

# Save PM2 config
pm2 save
pm2 startup
```

### Using Systemd (Linux)

Create service file:
```bash
sudo nano /etc/systemd/system/video-downloader-bot.service
```

Add content:
```ini
[Unit]
Description=Video Downloader Telegram Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/telegram_video_bot
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable video-downloader-bot
sudo systemctl start video-downloader-bot

# Check status
sudo systemctl status video-downloader-bot
```

### Using Docker

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

Build and run:
```bash
docker build -t video-downloader-bot .
docker run -d --name video-bot --env-file .env video-downloader-bot
```

## Bot Commands

| Command | Description | Access |
|---------|-------------|--------|
| /start | Start the bot | All |
| /help | Show help message | All |
| /settings | User preferences | All |
| /stats | Download statistics | All |
| /admin | Admin panel | Admin |
| /stats all | Global statistics | Admin |
| /users | List all users | Admin |
| /broadcast | Broadcast message | Admin |
| /ban | Ban a user | Admin |
| /unban | Unban a user | Admin |
| /user_info | User details | Admin |
| /maintenance | Toggle maintenance | Admin |
| /logs | View logs | Admin |

## Getting Telegram Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Start a chat and send `/newbot`
3. Follow instructions to create your bot
4. Copy the provided token to your `.env` file

## Getting Admin ID

1. Open Telegram and search for [@userinfobot](https://t.me/userinfobot)
2. Start the bot to get your numeric user ID
3. Add this ID to `ADMIN_IDS` in your `.env` file

## Project Structure

```
telegram_video_bot/
├── bot.py                 # Main entry point
├── config.py              # Configuration
├── requirements.txt       # Dependencies
├── .env.example           # Environment template
├── .env                   # Your configuration (not in git)
├── README.md              # This file
├── database/
│   ├── __init__.py
│   ├── db.py              # SQLite database
│   └── models.py          # Data models
├── downloaders/
│   ├── __init__.py
│   ├── youtube.py         # YouTube downloader
│   └── instagram.py       # Instagram downloader
├── handlers/
│   ├── __init__.py
│   ├── start.py           # Start/help commands
│   ├── download.py        # URL processing & downloads
│   ├── admin.py           # Admin commands
│   ├── settings.py        # User settings
│   └── callbacks.py       # Inline button handlers
├── utils/
│   ├── __init__.py
│   ├── helpers.py         # Utility functions
│   ├── keyboard.py        # Inline keyboards
│   └── progress.py        # Progress tracking
├── downloads/             # Temporary download folder
└── logs/                  # Log files
```

## Troubleshooting

### Bot not responding
- Check if BOT_TOKEN is correct
- Ensure bot is started with no webhook conflicts
- Check logs in `logs/bot.log`

### Downloads failing
- Ensure FFmpeg is installed
- Check disk space
- Verify YouTube/Instagram content is public

### Instagram download issues
- Add Instagram credentials for private content
- Add RapidAPI key as fallback method

### File too large
- Telegram has 50MB limit for bots
- Use lower quality settings
- Enable audio-only mode for music

## License

This project is for educational purposes. Respect copyright laws and terms of service of respective platforms.

## Support

For issues and feature requests, please contact the admin.
