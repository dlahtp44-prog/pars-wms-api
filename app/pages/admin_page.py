# app/pages/admin_page.py
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import get_history, admin_password_ok

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")

def is_admin(request: Request) -> bool:
    return bool(request.session.get("is_admin"))

@router.get("")
def page(request: Request):
    if not is_admin(request):
        return templates.TemplateResponse("admin_login.html", {"request": request, "msg": ""})
    rows = get_history(300)
    return templates.TemplateResponse("admin.html", {"request": request, "rows": rows})

@router.post("/login")
def login(request: Request, password: str = Form(...)):
    if admin_password_ok(password):
        request.session["is_admin"] = True
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse("admin_login.html", {"request": request, "msg": "비밀번호가 틀렸습니다."})

@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/admin", status_code=303)
