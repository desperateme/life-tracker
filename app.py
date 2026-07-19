"""人生修仙录 — FastAPI 入口"""
import sys
import secrets
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

# 确保 UTF-8 编码
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

from database import init_db
from auth import is_authenticated, ADMIN_PASSWORD, sign_token
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


# ===== 认证中间件 =====
PUBLIC_PATHS = ["/login", "/logout", "/health", "/ping", "/test", "/static", "/favicon.ico"]


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """全局认证：未登录只能访问公开路径，其余全部重定向到登录页"""
    request.state.is_authenticated = is_authenticated(request)

    is_public = any(request.url.path.startswith(p) for p in PUBLIC_PATHS)
    if not is_public and not is_authenticated(request):
        return RedirectResponse(url=f"/login?next={request.url.path}", status_code=303)

    response = await call_next(request)
    return response


# ===== 登录 / 登出 =====
@app.get("/login")
def login_page(request: Request, next: str = "/"):
    """登录页（GET）"""
    if is_authenticated(request):
        return RedirectResponse(url=next, status_code=303)
    return app.state.templates.TemplateResponse("login.html", {
        "request": request,
        "error": None,
        "next": next,
    })


@app.post("/login")
def login_action(request: Request, password: str = Form(""), next: str = Form("/")):
    """登录操作（POST）"""
    if password == ADMIN_PASSWORD:
        token = sign_token(secrets.token_hex(32))
        response = RedirectResponse(url=next, status_code=303)
        response.set_cookie(
            key="xiuxian_auth",
            value=token,
            httponly=True,
            max_age=365 * 24 * 3600,  # 一年有效期
            samesite="lax",
        )
        return response
    return app.state.templates.TemplateResponse("login.html", {
        "request": request,
        "error": "密码错误，道心不稳 ⚠️",
        "next": next,
    })


@app.get("/logout")
def logout():
    """登出"""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("xiuxian_auth")
    return response


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
