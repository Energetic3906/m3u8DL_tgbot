FROM python:3.11-slim-bookworm as builder
ADD requirements.txt /tmp/
RUN pip3 install --user -r /tmp/requirements.txt && rm /tmp/requirements.txt

# 使用官方的Python 3镜像
FROM python:3.11-slim-bookworm

# 设置工作目录
WORKDIR /app
# 复制所有文件到容器中
COPY . .

# 安装依赖
RUN apt update && apt install -y ffmpeg && \
    chmod +x /app/N_m3u8DL-RE

COPY --from=builder /root/.local /usr/local


# 在容器中运行你的Python脚本
CMD ["python3", "main.py"]