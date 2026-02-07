FROM python:3.9-slim

# 安装 ffmpeg（视频截图必须的系统工具） + libsndfile1（音频常见依赖）
RUN apt-get update && \
    apt-get install -y ffmpeg libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先复制依赖文件，安装 Python 包（用国内源加速）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目所有文件
COPY . .

# 暴露 Streamlit 端口
EXPOSE 8501

# 启动命令：把 "app.py" 改成你的实际主文件名（比如 main.py 或你的 Streamlit 文件名）
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=false"]
