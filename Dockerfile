# PM 智投 · 云端部署镜像（显式 COPY，避免 .dockerignore 失效问题）
FROM python:3.12-slim

WORKDIR /app

# 依赖层（利用 Docker 缓存）
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 只复制运行所需文件 —— 明确不包含 data/ 目录，从源头排除敏感数据
COPY main.py llm.py parsers.py prompts.py sanitize.py storage.py ./
COPY static/ ./static/
COPY start.sh start.bat ./
COPY README.md LICENSE ./
COPY Dockerfile render.yaml ./

# 确保 /app/data 目录存在但为空（程序会在此处创建 config.json / history.json，运行时数据）
RUN mkdir -p /app/data

# 云端监听 0.0.0.0，端口由平台注入（Render 用 $PORT）
ENV PM_SCOUT_HOST=0.0.0.0
EXPOSE 8765

CMD ["python", "main.py"]