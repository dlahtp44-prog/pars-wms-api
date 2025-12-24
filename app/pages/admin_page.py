from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from app.db import admin_password_ok, get_history, rollback

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def admin_home(request: Request):
    if request.session.get("is_admin") != True:
        return templates.TemplateResponse("admin_login.html", {"request": request, "err": ""})
    rows = get_history(500)
    return templates.TemplateResponse("admin.html", {"request": request, "rows": rows})

@router.post("/login")
def admin_login(request: Request, pw: str = Form(...)):
    if admin_password_ok(pw):
        request.session["is_admin"] = True
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse("admin_login.html", {"request": request, "err": "비밀번호가 틀렸습니다."})

@router.post("/logout")
def admin_logout(request: Request):
    request.session["is_admin"] = False
    return RedirectResponse("/admin", status_code=303)

@router.post("/rollback/{tx_id}")
def admin_rollback(request: Request, tx_id: int):
    if request.session.get("is_admin") != True:
        return RedirectResponse("/admin", status_code=303)
    rollback(tx_id)
    return RedirectResponse("/admin", status_code=303)
