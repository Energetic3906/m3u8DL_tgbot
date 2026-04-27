[中文](https://github.com/rule-airport/m3u8DL_tgbot/blob/main/README.md)

> "Premium" refers to premium users of Telegram, who have the capability to download files larger than 2 GB.

## Features

- Direct m3u8 URL download support
- Webpage URL support with automatic video detection (using yt-dlp)
- Automatic MP4 conversion
- Telegram Premium support for files >2GB

## Quick Start (Docker Deployment)

### 1. Initialize Configuration

```shell
# Copy configuration file
cp docker-compose.yml.default docker-compose.yml

# Create session storage directory
mkdir -p sessions
```

### 2. Fill in Configuration

Edit the environment variables in `docker-compose.yml`:

```yaml
environment:
  - APP_ID=<your_app_id>
  - APP_HASH=<your_app_hash>
  - TOKEN=<your_bot_token>
  - PREMIUM=False
  - AUTHORIZED_USERS=<your_user_id, comma-separated for multiple>
```

### 3. First Run (Auto-create Session)

```shell
docker-compose run --rm m3u8dl-bot
```

### 4. Normal Operation

```shell
# Run in background
docker-compose up -d

# View logs
docker-compose logs -f
```

## Usage

### Send direct m3u8 URL

```
https://example.com/video.m3u8
```

### Send webpage URL (auto-detect video)

Send any webpage URL containing video, bot will automatically detect and download using yt-dlp:

```
https://example.com/video-page.html
```

Caption format after download:
```
{title}

{original_url}
```

## Session Persistence

Session files are stored in `sessions/` directory and persist across image updates.

## Local Development

```shell
pip install pyrogram ffmpeg-python tqdm fakeredis tgcrypto yt-dlp && sudo apt-get install -y ffmpeg
python3 docker/main.py
```

## Configuration Reference

| Environment Variable | Description |
|---------------------|-------------|
| `APP_ID` | Telegram API ID |
| `APP_HASH` | Telegram API Hash |
| `TOKEN` | Telegram Bot Token |
| `PREMIUM` | `True` to enable premium mode (supports files >2GB) |
| `AUTHORIZED_USERS` | Authorized user IDs, comma-separated |

## Download Flow

1. Receive URL, try yt-dlp first to check support
2. If yt-dlp supports it, get title and download
3. If yt-dlp doesn't support, fallback to N_m3u8DL-RE
4. Auto-convert non-MP4 formats to MP4
5. Upload to Telegram

## Quote

This project is mainly based on [N_m3u8DL-RE](https://github.com/nilaoda/N_m3u8DL-RE) for secondary development, please follow the relevant agreement. Thanks to [nilaoda](https://github.com/nilaoda).
