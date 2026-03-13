# 使用Python 3.9官方镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DPLAYER_CONFIG_DIR=/config \
    DPLAYER_DATA_DIR=/data \
    DPLAYER_LOG_DIR=/logs \
    DPLAYER_THUMBNAIL_DIR=/data/thumbnails \
    DPLAYER_VIDEO_DIR=/data/videos

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY app.py .
COPY models.py .
COPY thumbnail_service.py .
COPY thumbnail_service_client.py .
COPY config_manager.py .
COPY templates/ ./templates/
COPY static/ ./static/

# 创建必要的目录
RUN mkdir -p /config /data /data/thumbnails /data/videos /logs /app/static/thumbnails

# 设置权限
RUN chmod -R 755 /app /config /data /logs

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:80/health', timeout=5)" || exit 1

# 启动命令
CMD ["python", "app.py"]
