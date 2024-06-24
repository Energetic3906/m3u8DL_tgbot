[中文](https://github.com/rule-airport/m3u8DL_tgbot/blob/main/README.md)

> "Premium" refers to premium users of Telegram, who have the capability to download files larger than 2 GB.

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

On first run, the bot will automatically detect if sessions exist. If not, it will guide you through creation:

- **Regular users**: Just enter your phone number to verify your Telegram account
- **Premium users**: After phone verification, the app_user session will also be created for sending large files

### 4. Normal Operation

After sessions are created, startup no longer requires interaction:

```shell
# Run in background
docker-compose up -d

# View logs
docker-compose logs -f
```

## Local Development

```shell
pip install pyrogram ffmpeg-python tqdm fakeredis tgcrypto && sudo apt-get install -y ffmpeg
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

## Quote

This project is mainly based on [N_m3u8DL-RE](https://github.com/nilaoda/N_m3u8DL-RE) for secondary development, please follow the relevant agreement. Thanks to [nilaoda](https://github.com/nilaoda).
