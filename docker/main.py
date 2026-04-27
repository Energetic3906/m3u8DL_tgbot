import os
import logging
import pathlib
from pyrogram import Client, filters, types, enums
from downloader import download_and_upload_video
from webpage import is_ytdlp_supported

def cleanup_stray_sessions():
    """Remove stray session directories from /app/ root (not in /app/sessions/)"""
    app_dir = "/app"
    stray_sessions = ["ytdl-main.session", "app_user.session"]
    for session_name in stray_sessions:
        session_path = os.path.join(app_dir, session_name)
        if os.path.isdir(session_path):
            if not os.listdir(session_path):
                os.rmdir(session_path)


def cleanup_cache():
    """Clean up download cache directories."""
    import shutil
    cache_paths = [
        "/tmp/m3u8D/cache",
        "/tmp/m3u8D/downloading"
    ]
    for cache_path in cache_paths:
        if os.path.exists(cache_path):
            try:
                for item in os.listdir(cache_path):
                    item_path = os.path.join(cache_path, item)
                    try:
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                    except Exception as e:
                        logging.warning(f"Failed to remove {item_path}: {e}")
                logging.info(f"Cache cleaned: {cache_path}")
            except Exception as e:
                logging.warning(f"Failed to clean {cache_path}: {e}")

# Initialize the Pyrogram client
api_id = os.environ.get("APP_ID")
api_hash = os.environ.get("APP_HASH")
bot_token = os.environ.get("TOKEN")
PREMIUM = os.environ.get("PREMIUM") == 'True'

logging.basicConfig(level=logging.INFO)
logging.info("PREMIUM: " + str(PREMIUM))

# Clean up any stray session directories from previous runs
cleanup_stray_sessions()

# Clean up download cache from previous runs
cleanup_cache()

session_dir = "/app/sessions"
os.makedirs(session_dir, exist_ok=True)

if PREMIUM:
    app_user = Client("app_user", workdir=session_dir)
app = Client("ytdl-main", api_id=api_id, api_hash=api_hash, bot_token=bot_token, workdir=session_dir)

authorized_users_env = os.environ.get("AUTHORIZED_USERS")
AUTHORIZED_USERS = [int(user_id) for user_id in authorized_users_env.split(",")] if authorized_users_env else []


@app.on_message(filters.command(["start"]))
def start_handler(client: Client, message: types.Message):
    logging.info("Welcome to m3u8DL bot!")
    client.send_message(message.chat.id, "Welcome to m3u8DL bot!")


@app.on_message(filters.command(["help"]))
def help_handler(client: Client, message: types.Message):
    help_text = """
**m3u8DL Bot 使用帮助**

**1. 直接发送 URL**
直接发送视频页面链接或 m3u8 链接，bot 会自动检测并下载。

**2. 自定义标题格式**
发送: `download_url,name,display_url`

示例:
```
https://example.com/video.m3u8,视频标题,https://youtube.com/watch?v=xxx
```

- `download_url`: 要下载的 URL（可以是 m3u8 或视频页面）
- `name`: 自定义标题
- `display_url`: 显示在消息中的来源链接

**3. 支持的功能**
- 直接下载 m3u8 链接
- 自动从网页提取视频（yt-dlp）
- 自动转换 MP4 格式
- 支持 Telegram Premium 用户发送大文件

**4. 示例**
```
https://youtube.com/shorts/xxx
```
或
```
https://example.com/video.m3u8,我的视频标题,https://youtube.com/shorts/xxx
```
"""
    client.send_message(message.chat.id, help_text, disable_web_page_preview=True)


@app.on_message(filters.incoming & (filters.text | filters.document))
def handle_message(client: Client, message: types.Message):
    chat_id = message.from_user.id
    client.send_chat_action(chat_id, enums.ChatAction.TYPING)
    user_message = message.text

    if chat_id not in AUTHORIZED_USERS:
        client.send_message(chat_id, "You are not authorized to use this bot.")
        return

    # Parse message: check for "download_url,name,display_url" format
    download_url = None
    custom_title = None
    display_url = None

    parts = user_message.split(",")
    if len(parts) >= 3:
        # format: download_url,name,display_url
        potential_download_url = parts[0].strip()
        potential_title = parts[1].strip()
        potential_display_url = ",".join(parts[2:]).strip()  # handle URLs with commas

        if potential_download_url.startswith("https://") or potential_download_url.startswith("http://"):
            download_url = potential_download_url
            custom_title = potential_title
            display_url = potential_display_url
            logging.info(f"Custom format: download='{download_url}', title='{custom_title}', display='{display_url}'")

    # If not custom format, use standard URL handling
    if not download_url:
        if not (user_message.startswith("https://") or user_message.startswith("http://")):
            client.send_message(chat_id, "Please provide a valid URL.")
            return

        download_url = user_message

        # If it's a direct m3u8 URL, use it directly
        if ".m3u8" in user_message.lower():
            logging.info(f"Direct m3u8 URL detected: {user_message}")
        else:
            # Try to use yt-dlp to get video info
            logging.info(f"Checking with yt-dlp: {user_message}")
            is_supported, title, m3u8_url = is_ytdlp_supported(user_message)

            if is_supported and title:
                custom_title = title
                logging.info(f"yt-dlp found: {title}")

                if m3u8_url:
                    download_url = m3u8_url
                    logging.info(f"yt-dlp extracted m3u8 URL: {m3u8_url}")
            else:
                logging.info(f"yt-dlp not supported, trying N_m3u8DL-RE: {user_message}")

    save_dir = "/tmp/m3u8D/cache"
    os.makedirs(save_dir, exist_ok=True)

    # Start download
    text = "Your task was added to active queue.\nProcessing...\n\n"
    bot_msg = message.reply_text(text, quote=True)

    try:
        if PREMIUM:
            download_and_upload_video(app_user, client, bot_msg, download_url, save_dir, custom_title, display_url, is_premium=True)
        else:
            download_and_upload_video(app, client, bot_msg, download_url, save_dir, custom_title, display_url, is_premium=False)
    except Exception as e:
        logging.error(f"Download failed: {e}")
        client.send_message(chat_id, f"Download failed: {str(e)}")


# Start client
if PREMIUM:
    app_user.start()
    app.run()
else:
    app.run()
