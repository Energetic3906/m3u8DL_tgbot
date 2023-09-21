[中文](https://github.com/rule-airport/m3u8DL_tgbot/blob/main/README_CN.md)

> "Premium" refers to premium users of Telegram, who have the capability to download files larger than 2 GB.

## How to Use Premium Features

To begin with, you need to obtain an `app_user`. Here are the steps:

**Step 1:** Create a file named `get_session.py`:

```python
from pyrogram import Client, filters, types, enums

api_id = 
api_hash = "" 
bot_token = ""
phone_number = "" 

app_user = Client("app_user", api_id=api_id, api_hash=api_hash, phone_number=phone_number)

app_user.run()
```

Run the following command in your terminal:

```shell
python3 get_session.py
```

You will be prompted to enter a verification code and your account password. After that, exit by pressing Ctrl+C.

**Step 2:** Modify the `get_session.py` file:

```python
from pyrogram import Client, filters, types, enums

api_id = 
api_hash = "" 
bot_token = ""
phone_number = "" 

app_user = Client("app_user", api_id=api_id, api_hash=api_hash, phone_number=phone_number)
app = Client("ytdl-main", api_id=api_id, api_hash=api_hash, bot_token=bot_token, ipv6=False)

app_user.start()
app.run()
```

Run the following command again:

```shell
python3 get_session.py
```

Once this is done, two session files, `app_user.session` and `ytdl-main.session`, will be generated in your current directory. Now, in the `main.py` file, input your own account ID to create a private bot:

```python
AUTHORIZED_USERS = [user_id]
```

Finally, run:

```shell
python3 main.py
```

## How Regular Users Can Use It

For regular users, follow these steps:

1. Remove the lines `app_user = Client("app_user")` and `app_user.start()` in the `main.py` file.

2. Change all instances of `app_user.send_video` to `client.send_video` in the `main.py` file.

Modify the `main.py` file as follows:

```python
app = Client("ytdl-main", api_id=api_id, api_hash=api_hash, bot_token=bot_token, ipv6=False)
```

Finally, run:

```shell
python3 main.py
```
