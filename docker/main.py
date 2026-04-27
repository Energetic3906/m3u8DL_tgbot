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

# Initialize the Pyrogram client
api_id = os.environ.get("APP_ID")
api_hash = os.environ.get("APP_HASH")
bot_token = os.environ.get("TOKEN")
PREMIUM = os.environ.get("PREMIUM") == 'True'

logging.basicConfig(level=logging.INFO)
logging.info("PREMIUM: " + str(PREMIUM))

# Clean up any stray session directories from previous runs
cleanup_stray_sessions()

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


@app.on_message(filters.incoming & (filters.text | filters.document))
def handle_message(client: Client, message: types.Message):
    chat_id = message.from_user.id
    client.send_chat_action(chat_id, enums.ChatAction.TYPING)
    user_message = message.text

    if chat_id not in AUTHORIZED_USERS:
        client.send_message(chat_id, "You are not authorized to use this bot.")
        return

    if not (user_message.startswith("https://") or user_message.startswith("http://")):
        client.send_message(chat_id, "Please provide a valid URL.")
        return

    save_dir = "/tmp/m3u8D/cache"
    os.makedirs(save_dir, exist_ok=True)

    # Determine download source and title
    download_url = user_message
    custom_title = None

    # If it's a direct m3u8 URL, use it directly
    if ".m3u8" in user_message.lower():
        download_url = user_message
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
                # yt-dlp found title but no direct m3u8 URL
                # Use original URL - yt-dlp or N_m3u8DL-RE will handle it
                logging.info(f"Using original URL for download: {user_message}")
        else:
            # yt-dlp doesn't support this URL - try N_m3u8DL-RE directly
            logging.info(f"yt-dlp not supported, trying N_m3u8DL-RE: {user_message}")

    # Start download
    text = "Your task was added to active queue.\nProcessing...\n\n"
    bot_msg = message.reply_text(text, quote=True)

    try:
        if PREMIUM:
            download_and_upload_video(app_user, client, bot_msg, download_url, save_dir, custom_title)
        else:
            download_and_upload_video(app, client, bot_msg, download_url, save_dir, custom_title)
    except Exception as e:
        logging.error(f"Download failed: {e}")
        client.send_message(chat_id, f"Download failed: {str(e)}")


# Start client
if PREMIUM:
    app_user.start()
    app.run()
else:
    app.run()
