FROM python:3.9-slim

# 安装系统依赖：ffmpeg（用于视频截图） + libsndfile1（音频处理常见依赖，whisper 可能需要）
RUN apt-get update && \
    apt-get install -y ffmpeg libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 先复制 requirements.txt 安装依赖（用国内清华源加速 pip，东京 IP 也能快点）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有项目文件
COPY . .

# 暴露 Streamlit 默认端口
EXPOSE 8501

# 启动命令：使用你的主文件 video_screenshot_app.py
CMD ["streamlit", "run", "video_screenshot_app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=false"]
