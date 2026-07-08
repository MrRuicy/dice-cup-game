"""
Gradio 封装应用 - 用于魔搭社区部署
将 FastAPI 后端和 Vue 前端封装为 Gradio 应用
"""
import gradio as gr
import uvicorn
import threading
import time
from pathlib import Path
from main import app as fastapi_app
from fastapi.staticfiles import StaticFiles

# 挂载前端静态文件
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    fastapi_app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
else:
    print("⚠️  警告: static/ 目录不存在，请先构建前端")

# 在后台线程启动 FastAPI 服务器
def start_backend():
    """启动 FastAPI WebSocket 服务器"""
    print("🚀 启动后端服务...")
    uvicorn.run(
        fastapi_app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

backend_thread = threading.Thread(target=start_backend, daemon=True)
backend_thread.start()

# 等待后端启动
time.sleep(2)

# Gradio 界面：内嵌前端
with gr.Blocks(
    title="🎲 骰盅游戏",
    theme=gr.themes.Soft(),
    css="""
        body { margin: 0; padding: 0; overflow: hidden; }
        .gradio-container { padding: 0 !important; }
        iframe { border: none; display: block; }
    """
) as demo:
    gr.HTML("""
    <div style="width: 100%; height: 100vh; margin: 0; padding: 0; overflow: hidden;">
        <iframe
            src="http://localhost:8000"
            width="100%"
            height="100%"
            frameborder="0"
            style="border: none; display: block;">
        </iframe>
    </div>
    """)

if __name__ == "__main__":
    print("✨ 骰盅游戏启动中...")
    print("📍 前端地址: http://localhost:8000")
    print("📍 Gradio 界面: http://localhost:7860")

    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
