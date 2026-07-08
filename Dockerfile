FROM python:3.10-slim

WORKDIR /app

# 复制依赖文件并安装
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ backend/

# 复制前端构建产物
COPY frontend/dist/ frontend/dist/

# 暴露端口
EXPOSE 7860

# 启动服务
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
