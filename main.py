import os
import logging
import pathlib
from pyrogram import Client, filters, types, enums
from downloader import download_and_upload_video

# Initialize the Pyrogram client
# api_id =   # Replace with your actual api_id
# api_hash = ""  # Replace with your actual api_hash
# bot_token = ""  # Replace with your actual bot_token
# phone_number = ""  # Replace with your actual phone number

app_user = Client("app_user")
app = Client("ytdl-main")
# Only authenticated users can use the bot and enter the account ID.
AUTHORIZED_USERS = [userid,userid-2]

@app.on_message(filters.command(["start"]))
def start_handler(client: Client, message: types.Message):
    from_id = message.from_user.id
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

    if user_message.startswith("https://") or user_message.startswith("http://"):
        # Create a temporary directory for the downloaded video
        save_dir = "/tmp/m3u8D/cache"  # Replace with your temporary directory path
        os.makedirs(save_dir, exist_ok=True)

        # Tell the user that the url has been added to the download queue.
        text = "Your task was added to active queue.\nProcessing...\n\n"
        bot_msg: typing.Union[types.Message, typing.Coroutine] = message.reply_text(text, quote=True)

        download_and_upload_video(app_user, client, bot_msg, user_message, save_dir)

    else:
        client.send_message(chat_id, "Please provide a valid URL.")


# Start client
app_user.start()
app.run()