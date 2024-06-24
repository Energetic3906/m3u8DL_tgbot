[English](https://github.com/rule-airport/m3u8DL_tgbot/blob/main/README_EN.md)

> premium 指的是 telegram 的 premium 用户。为了下载超过 2G 的文件。

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

首次运行时会自动检测 session 是否存在，如果不存在会引导你创建：

- **普通用户**：只需输入手机号验证 Telegram 账号
- **Premium 用户**：输入手机号后，还会创建 app_user session 用于发送大文件

### 4. 正常运行

Session 创建完成后，以后启动不再需要交互：

```shell
# 后台运行
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 本地开发

```shell
pip install pyrogram ffmpeg-python tqdm fakeredis tgcrypto && sudo apt-get install -y ffmpeg
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

## 引用

本项目主要基于 [N_m3u8DL-RE](https://github.com/nilaoda/N_m3u8DL-RE) 进行的二次开发，请遵循相关协议。感谢 [nilaoda](https://github.com/nilaoda)
