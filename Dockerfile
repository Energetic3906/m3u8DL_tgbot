# 使用官方的Python 3镜像
FROM python:3.11-slim-bookworm

# 设置工作目录
WORKDIR /app

# 复制所有文件到容器中
COPY . .

# 安装依赖
RUN apt update && apt install -y ffmpeg && \
    pip3 install --no-cache-dir -r requirements.txt && \
    chmod +x /app/N_m3u8DL-RE

# 在容器中运行你的Python脚本
CMD ["python3", "main.py"]