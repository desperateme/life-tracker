"""人生修仙录 — FastAPI 入口"""
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

# 确保 UTF-8 编码
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

from database import init_db
from routes import dashboard, learning, fitness, discipline, tasks, earning, finance, progress


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时初始化数据库"""
    init_db()
    yield


# 创建应用
app = FastAPI(title="人生修仙录", version="1.0", lifespan=lifespan)

# 模板 & 静态文件
BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# 直接用 Jinja2 Environment（绕过 Starlette 的 Jinja2Templates 缓存 bug）
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class SimpleTemplates:
    """简单的模板包装器，避免 Starlette Jinja2Templates 的缓存问题"""
    def __init__(self, env: Environment):
        self.env = env

    def TemplateResponse(self, name: str, context: dict):
        template = self.env.get_template(name)
        rendered = template.render(**context)
        return HTMLResponse(rendered)


app.state.templates = SimpleTemplates(jinja_env)

print(f"[启动] TEMPLATE_DIR={TEMPLATE_DIR}", flush=True)

# 注册路由
@app.get("/health")
def health():
    """健康检查"""
    return {"status": "ok", "templates": TEMPLATE_DIR, "static": STATIC_DIR}

@app.get("/ping")
def ping(request: Request):
    """测试模板渲染"""
    import traceback
    try:
        return app.state.templates.TemplateResponse("base.html", {"request": request})
    except Exception as e:
        from fastapi.responses import HTMLResponse
        return HTMLResponse(f"<pre>Template error: {e}\n{traceback.format_exc()}</pre>")

@app.get("/test")
def test_html():
    """纯 HTML 测试"""
    from fastapi.responses import HTMLResponse
    return HTMLResponse("<h1>Hello World</h1>")

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
