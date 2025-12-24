from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from app.db import get_history, admin_password_ok

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def admin(request: Request):
    if request.session.get("is_admin") is True:
        rows = get_history(limit=300)
        return templates.TemplateResponse("admin.html", {"request": request, "rows": rows})
    return templates.TemplateResponse("admin.html", {"request": request, "rows": [], "need_login": True})

@router.post("/login")
def admin_login(request: Request, password: str = Form(...)):
    if admin_password_ok(password):
        request.session["is_admin"] = True
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse("admin.html", {"request": request, "rows": [], "need_login": True, "error": "비밀번호 오류"})

@router.post("/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/admin", status_code=303)
