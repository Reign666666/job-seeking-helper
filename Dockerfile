# PM 智投 · 云端部署镜像
FROM python:3.12-slim

WORKDIR /app

# 依赖层（利用 Docker 缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 应用代码
COPY . .

# 云端监听 0.0.0.0，端口由平台注入（Render 用 $PORT）
ENV PM_SCOUT_HOST=0.0.0.0
EXPOSE 8765

CMD ["python", "main.py"]
