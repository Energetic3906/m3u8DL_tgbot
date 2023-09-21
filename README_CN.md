[English](https://github.com/rule-airport/m3u8DL_tgbot/blob/main/README.md)
> premium 指的是 telegram 的 premium 用户。为了下载超过 2G 的文件。

## premium 用户使用

首先获得 app_user
第一步新建 `get_session.py` ：

```python
from pyrogram import Client, filters, types, enums
api_id = 
api_hash = "" 
bot_token = ""
phone_number = "" 

app_user = Client("app_user", api_id=api_id, api_hash=api_hash, phone_number=phone_number)

app_user.run()
```

```shell
python3 get_session.py
```

输入验证码和账号密码。然后 Ctrl+C 退出，然后修改 `get_session.py` ：

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

```shell
python3 get_session.py
```

运行之后，会在当前文件夹里面生成 `app_user.session` 和 `ytdl-main.session`，然后在 `main.py` 中输入自己的账户 ID，这样就可以生成私有 bot。

`AUTHORIZED_USERS = [user_id]`

最后运行：

```shell
python3 main.py
```

## 普通用户使用

删除 `main.py` 中的 `app_user = Client("app_user")` ，`app_user.start()` ；将 `app_user.send_video` 修改为 `client.send_video`。

修改 `main.py` ：

```python
app = Client("ytdl-main", api_id=api_id, api_hash=api_hash, bot_token=bot_token, ipv6=False)
```

最后运行：

```shell
python3 main.py
```

