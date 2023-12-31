# 构建阶段
FROM python:3.11-slim-bookworm as builder
ADD requirements.txt /tmp/
RUN pip3 install --user --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY docker /tmp/app

RUN chmod +x /tmp/app/N_m3u8DL-RE

# 最终阶段
FROM python:3.11-slim-bookworm

# 设置工作目录
WORKDIR /app

# 从构建阶段复制依赖项
COPY --from=builder /root/.local /usr/local
COPY --from=builder /tmp/app .
# 安装依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends --no-install-suggests ffmpeg && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    rm -rf /var/cache/apt/archives/*

# 在容器中运行你的Python脚本
CMD ["python3", "main.py"]