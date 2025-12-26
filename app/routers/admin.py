from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/admin", tags=["Admin"])
templates = Jinja2Templates(directory="app/templates")

# ⚠️ A안 기준: 임시 관리자 인증 (세션/비밀번호 로직 제거)
@router.get("", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse(
        "admin.html",
        {"request": request}
    )
