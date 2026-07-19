"""人生修仙录 — FastAPI 入口"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from database import init_db
from routes import dashboard, learning, fitness, discipline, tasks, earning, finance, progress

# 初始化数据库
init_db()

# 创建应用
app = FastAPI(title="人生修仙录", version="1.0")

# 模板 & 静态文件
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# 将 templates 挂到 app.state 供路由使用
app.state.templates = templates

# 注册路由
app.include_router(dashboard.router)
app.include_router(learning.router)
app.include_router(fitness.router)
app.include_router(discipline.router)
app.include_router(tasks.router)
app.include_router(earning.router)
app.include_router(finance.router)
app.include_router(progress.router)

if __name__ == "__main__":
    import uvicorn
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("[人生修仙录] 启动中...")
    print("  打开浏览器访问: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
