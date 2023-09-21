import os
import logging
import pathlib
from pyrogram import Client, filters, types, enums
from downloader import ytdl_download, gen_cap, upload_hook, gen_video_markup

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
    markup = gen_video_markup()

    if chat_id not in AUTHORIZED_USERS:
        client.send_message(chat_id, "You are not authorized to use this bot.")
        return

    if user_message.startswith("https://") or user_message.startswith("http://"):
        try:
            # Create a temporary directory for the downloaded video
            temp_dir = "/tmp/m3u8D/cache"  # Replace with your temporary directory path
            os.makedirs(temp_dir, exist_ok=True)

            # Tell the user that the url has been added to the download queue.
            text = "Your task was added to active queue.\nProcessing...\n\n"
            bot_msg: typing.Union[types.Message, typing.Coroutine] = message.reply_text(text, quote=True)

            # Download the video
            video_paths = ytdl_download(user_message, temp_dir)

           
            chat_id = bot_msg.chat.id
            # Send the downloaded video to the user
            for video_path in video_paths:
                video_path_str = str(video_path)
                print("video_paths: ", video_path_str)
                cap, meta = gen_cap(bot_msg, user_message, video_path_str)
                print("cap: ", cap)
                print("meta: ", meta)
                app_user.send_video(
                    chat_id,
                    video_path_str,
                    caption=cap,
                    progress=upload_hook,
                    progress_args=(bot_msg,),
                    reply_markup=markup,
                    **meta
                )

            bot_msg.edit_text(f"Download success!✅✅✅")   

            # Delete all files and subdirectories
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except Exception as e:
                    logging.error(f"Failed to delete {item_path}: {str(e)}")   
            
            # delete directory
            try:
                os.rmdir(temp_dir)
            except OSError as e:
                if e.errno == errno.ENOTEMPTY:
                    pass  # If the directory is not empty, you can proceed further or report an error
                else:
                    raise  # If other errors occur, throw an exception
            
        except Exception as e:
            client.send_message(chat_id, f"Download failed: {str(e)}")
    
    else:
        client.send_message(chat_id, "Please provide a valid URL.")


# Start client
app_user.start()
app.run()