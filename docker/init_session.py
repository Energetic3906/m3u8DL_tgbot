import os
import sys

def init_sessions():
    from pyrogram import Client

    api_id = os.environ.get("APP_ID")
    api_hash = os.environ.get("APP_HASH")

    if not api_id or not api_hash:
        print("ERROR: APP_ID and APP_HASH environment variables are required.")
        sys.exit(1)

    session_dir = "/app"

    # ytdl-main.session (bot session)
    bot_session_path = os.path.join(session_dir, "ytdl-main.session")
    if os.path.exists(bot_session_path):
        print(f"[SKIP] {bot_session_path} already exists.")
    else:
        print("Creating ytdl-main.session (bot session)...")
        print("This session will use the bot token from TOKEN environment variable.")
        app = Client(
            "ytdl-main",
            api_id=api_id,
            api_hash=api_hash,
            bot_token=os.environ.get("TOKEN")
        )
        app.start()
        app.stop()
        print("ytdl-main.session created successfully!")

    # app_user.session (user session, for premium mode)
    PREMIUM = os.environ.get("PREMIUM") == 'True'
    if PREMIUM:
        user_session_path = os.path.join(session_dir, "app_user.session")
        if os.path.exists(user_session_path):
            print(f"[SKIP] {user_session_path} already exists.")
        else:
            print("Creating app_user.session (user session for premium mode)...")
            phone = input("Enter your phone number (with country code, e.g. +86138...): ").strip()
            app_user = Client(
                "app_user",
                api_id=api_id,
                api_hash=api_hash,
                phone_number=phone
            )
            app_user.start()
            app_user.stop()
            print("app_user.session created successfully!")
            print("\nIMPORTANT: Please add your user ID to AUTHORIZED_USERS in docker-compose.yml")
            print("Then restart the container with: docker-compose up -d")
    else:
        print("\n[INFO] PREMIUM=False, skipping app_user.session creation.")

if __name__ == "__main__":
    init_sessions()
