"""认证模块 — 简单的密码登录 + 签名 Cookie"""
import hashlib
import hmac
import os
from fastapi import Request
from fastapi.responses import RedirectResponse

SECRET_KEY = os.environ.get("SECRET_KEY", "xiuxian-life-tracker-secret-2024")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "xiuxian888")


def sign_token(token: str) -> str:
    """对 token 签名，返回 token.signature"""
    sig = hmac.new(SECRET_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()
    return f"{token}.{sig}"


def verify_token(signed: str) -> str | None:
    """验证签名，成功返回原始 token，失败返回 None"""
    try:
        token, sig = signed.rsplit(".", 1)
        expected = hmac.new(SECRET_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()
        return token if hmac.compare_digest(sig, expected) else None
    except (ValueError, AttributeError):
        return None


def is_authenticated(request: Request) -> bool:
    """检查当前请求是否已认证"""
    cookie = request.cookies.get("xiuxian_auth")
    if not cookie:
        return False
    return verify_token(cookie) is not None


def require_auth(request: Request):
    """FastAPI 依赖：未登录则重定向到登录页"""
    if not is_authenticated(request):
        return RedirectResponse(
            url=f"/login?next={request.url.path}", status_code=303
        )
    return None  # 已登录，继续执行
