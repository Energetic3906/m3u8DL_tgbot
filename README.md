[English](https://github.com/rule-airport/m3u8DL_tgbot/blob/main/README_EN.md)

> premium 指的是 telegram 的 premium 用户。为了下载超过 2G 的文件。

## 功能特性

- 支持直接发送 m3u8 URL 进行下载
- 支持发送网页 URL，bot 自动检测并提取视频（使用 yt-dlp）
- 自动转换为 MP4 格式
- 支持 Telegram Premium 用户发送大文件（>2GB）

## 快速开始（Docker 部署）

### 1. 初始化配置

```shell
# 复制配置文件
cp docker-compose.yml.default docker-compose.yml

# 创建 session 存储目录
mkdir -p sessions
```

### 2. 填写配置

编辑 `docker-compose.yml` 中的环境变量：

```yaml
environment:
  - APP_ID=<你的 APP_ID>
  - APP_HASH=<你的 APP_HASH>
  - TOKEN=<你的 BOT_TOKEN>
  - PREMIUM=False
  - AUTHORIZED_USERS=<你的用户 ID，多个用逗号分隔>
```

### 3. 首次运行（自动创建 Session）

```shell
docker-compose run --rm m3u8dl-bot
```

### 4. 正常运行

```shell
# 后台运行
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 使用方式

### 直接发送 m3u8 URL

```
https://example.com/video.m3u8
```

### 发送网页 URL（自动检测视频）

发送任意包含视频的网页 URL，bot 会使用 yt-dlp 自动检测并下载：

```
https://example.com/video-page.html
```

下载后的 caption 格式：
```
{视频标题}

{原始URL}
```

## Session 持久化

Session 文件存储在 `sessions/` 目录，更新镜像时不会丢失。

## 本地开发

```shell
pip install pyrogram ffmpeg-python tqdm fakeredis tgcrypto yt-dlp && sudo apt-get install -y ffmpeg
python3 docker/main.py
```

## 配置说明

| 环境变量 | 说明 |
|---------|------|
| `APP_ID` | Telegram API ID |
| `APP_HASH` | Telegram API Hash |
| `TOKEN` | Telegram Bot Token |
| `PREMIUM` | `True` 启用 premium 模式（支持 >2GB 文件） |
| `AUTHORIZED_USERS` | 授权用户 ID，多个用逗号分隔 |

## 下载流程

1. 收到 URL 后，先尝试使用 yt-dlp 检测是否支持
2. 如果 yt-dlp 支持，获取标题并下载
3. 如果 yt-dlp 不支持，回退使用 N_m3u8DL-RE 进行下载
4. 自动转换非 MP4 格式为 MP4
5. 上传到 Telegram

## 引用

本项目主要基于 [N_m3u8DL-RE](https://github.com/nilaoda/N_m3u8DL-RE) 进行的二次开发，请遵循相关协议。感谢 [nilaoda](https://github.com/nilaoda)
