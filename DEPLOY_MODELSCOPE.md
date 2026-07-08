# 魔搭社区创空间部署指南

## 📦 部署到 ModelScope（魔搭社区）

魔搭社区的创空间支持部署基于 Gradio/Streamlit 的应用，但对于标准 Web 应用（FastAPI + Vue），需要特殊配置。

---

## 方案一：Gradio 封装（推荐）

将骰盅游戏封装为 Gradio 应用，利用 Gradio 的 Web 服务器。

### 1. 安装 Gradio

```bash
cd backend
pip install gradio
```

### 2. 创建 Gradio 启动文件

创建 `backend/app_gradio.py`：

```python
import gradio as gr
import uvicorn
import threading
from main import app as fastapi_app

# 启动 FastAPI 后端
def start_backend():
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)

# 在后台线程启动 FastAPI
backend_thread = threading.Thread(target=start_backend, daemon=True)
backend_thread.start()

# Gradio 界面：内嵌前端
with gr.Blocks(title="骰盅游戏") as demo:
    gr.HTML("""
    <style>
        body { margin: 0; padding: 0; }
        iframe { border: none; }
    </style>
    <iframe 
        src="http://localhost:5173" 
        width="100%" 
        height="800px"
        frameborder="0">
    </iframe>
    """)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True
    )
```

### 3. 构建前端静态文件

```bash
cd frontend
npm run build
# 将 dist/ 复制到 backend/static/
cp -r dist ../backend/static
```

### 4. 修改 Gradio 应用以提供静态文件

更新 `backend/app_gradio.py`：

```python
import gradio as gr
import uvicorn
import threading
from pathlib import Path
from main import app as fastapi_app
from fastapi.staticfiles import StaticFiles

# 挂载前端静态文件
fastapi_app.mount("/", StaticFiles(directory="static", html=True), name="static")

# 启动 FastAPI 后端
def start_backend():
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)

backend_thread = threading.Thread(target=start_backend, daemon=True)
backend_thread.start()

# Gradio 界面：内嵌前端
with gr.Blocks(title="🎲 骰盅游戏") as demo:
    gr.HTML("""
    <div style="width: 100%; height: 100vh; margin: 0; padding: 0;">
        <iframe 
            src="http://localhost:8000" 
            width="100%" 
            height="100%"
            frameborder="0"
            style="border: none;">
        </iframe>
    </div>
    """)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
```

### 5. 创建 requirements.txt

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
websockets==12.0
gradio==4.19.2
```

### 6. 创建 README（魔搭必需）

创建项目根目录的 `README_MODELSCOPE.md`：

```markdown
---
title: 骰盅游戏
emoji: 🎲
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: 4.19.2
app_file: backend/app_gradio.py
pinned: false
---

# 🎲 骰盅游戏

实时多人在线骰盅游戏，支持房间管理、多轮投掷、幸运嘉宾机制。

## 特性
- 🎮 实时多人对战
- 🎲 流畅的骰盅动画
- ✨ 幸运嘉宾机制
- 📊 实时统计面板

## 使用方法
1. 点击"创建房间"
2. 设置骰子数量和口令（可选）
3. 分享房间号给好友加入
4. 开始游戏！
```

### 7. 上传到魔搭

1. 在魔搭社区创建新的创空间
2. 选择 SDK: **Gradio**
3. 上传以下文件：
   ```
   backend/
     ├── app_gradio.py
     ├── main.py
     ├── game.py
     ├── room.py
     ├── manager.py
     ├── protocol.py
     ├── static/  (前端构建产物)
     └── requirements.txt
   README_MODELSCOPE.md
   ```

---

## 方案二：Docker 部署（适用于支持 Docker 的平台）

如果魔搭支持自定义 Docker，可以使用此方案。

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装 Node.js
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

# 复制后端
COPY backend/ ./backend/
WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt

# 复制前端并构建
COPY frontend/ /app/frontend/
WORKDIR /app/frontend
RUN npm install && npm run build

# 将前端构建产物移到后端静态目录
RUN mv /app/frontend/dist /app/backend/static

# 回到后端目录
WORKDIR /app/backend

# 暴露端口
EXPOSE 7860

# 启动命令
CMD ["python", "app_gradio.py"]
```

### 构建和运行

```bash
docker build -t dice-game .
docker run -p 7860:7860 dice-game
```

---

## 方案三：静态站点 + Serverless（最简单）

如果只需要前端，后端使用第三方 WebSocket 服务。

### 前端修改

修改 `frontend/src/services/ws.ts` 中的 WebSocket 地址为你的服务器地址。

### 部署前端到魔搭

1. 构建前端：
   ```bash
   cd frontend
   npm run build
   ```

2. 上传 `dist/` 目录到魔搭的静态站点托管

### 后端独立部署

后端部署到其他平台（如阿里云、腾讯云），然后配置 CORS。

---

## 注意事项

### 1. WebSocket 支持

魔搭创空间需要确认是否支持 WebSocket。如果不支持，需要：
- 使用轮询（Polling）代替 WebSocket
- 或将后端部署到支持 WebSocket 的平台

### 2. 端口限制

魔搭 Gradio 应用默认使用 **7860** 端口，确保应用监听此端口。

### 3. 文件大小限制

魔搭可能有文件大小限制，确保：
- 前端构建产物 < 100MB
- 依赖包合理精简

### 4. CORS 配置

如果前后端分离部署，需要在后端配置 CORS：

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境改为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 快速部署脚本

创建 `deploy_modelscope.sh`：

```bash
#!/bin/bash
set -e

echo "🚀 准备部署到魔搭社区..."

# 1. 构建前端
echo "📦 构建前端..."
cd frontend
npm install
npm run build

# 2. 复制到后端
echo "📋 复制静态文件..."
rm -rf ../backend/static
cp -r dist ../backend/static

# 3. 创建部署包
echo "📦 打包..."
cd ..
mkdir -p deploy_package
cp -r backend/* deploy_package/
cp README_MODELSCOPE.md deploy_package/README.md

echo "✅ 部署包已准备完成: deploy_package/"
echo "请上传 deploy_package/ 目录到魔搭创空间"
```

运行：

```bash
chmod +x deploy_modelscope.sh
./deploy_modelscope.sh
```

---

## 测试本地运行

在上传到魔搭前，先本地测试：

```bash
# 构建前端
cd frontend
npm run build
cp -r dist ../backend/static

# 运行 Gradio 应用
cd ../backend
pip install -r requirements.txt
python app_gradio.py
```

访问 `http://localhost:7860`

---

## 常见问题

### Q: WebSocket 连接失败？
A: 检查魔搭是否支持 WebSocket，如不支持需改用轮询。

### Q: 前端静态文件 404？
A: 确认 `backend/static/` 目录包含 `index.html` 和所有资源。

### Q: 应用启动慢？
A: 魔搭冷启动需要时间，建议使用付费实例保持常驻。

---

需要帮助？
- 魔搭社区文档：https://www.modelscope.cn/docs
- 创空间指南：https://www.modelscope.cn/docs/ModelScope%20Spaces
