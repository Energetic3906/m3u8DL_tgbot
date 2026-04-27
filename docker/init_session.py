import os
import sys
import shutil

def cleanup_stray_sessions():
    """Remove stray session directories from /app/ root (not in /app/sessions/)"""
    app_dir = "/app"
    sessions_dir = "/app/sessions"

    stray_sessions = ["ytdl-main.session", "app_user.session"]
    for session_name in stray_sessions:
        session_path = os.path.join(app_dir, session_name)
        if os.path.isdir(session_path):
            # Check if it's empty
            if not os.listdir(session_path):
                print(f"[CLEANUP] Removing empty directory: {session_path}")
                os.rmdir(session_path)
            else:
                print(f"[WARNING] {session_path} is not empty, skipping cleanup")

def init_sessions():
    from pyrogram import Client

    api_id = os.environ.get("APP_ID")
    api_hash = os.environ.get("APP_HASH")

    if not api_id or not api_hash:
        print("ERROR: APP_ID and APP_HASH environment variables are required.")
        sys.exit(1)

    # Clean up any stray session directories from previous runs
    cleanup_stray_sessions()

    session_dir = "/app/sessions"
    os.makedirs(session_dir, exist_ok=True)

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
            bot_token=os.environ.get("TOKEN"),
            workdir=session_dir
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
                phone_number=phone,
                workdir=session_dir
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