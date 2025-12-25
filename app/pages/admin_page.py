# app/pages/admin_page.py
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.db import admin_password_ok, get_history, rollback

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")

def is_admin(request: Request) -> bool:
    return bool(request.session.get("is_admin"))

@router.get("")
def admin_home(request: Request):
    if not is_admin(request):
        return templates.TemplateResponse("admin_login.html", {"request": request, "err": ""})
    rows = get_history(300)
    return templates.TemplateResponse("admin.html", {"request": request, "rows": rows})

@router.post("/login")
def admin_login(request: Request, password: str = Form(...)):
if not admin_password_ok(password):
    return templates.TemplateResponse(
        "admin_login.html",
        {"request": request, "error": "비밀번호가 틀렸습니다"}
    )


@router.get("/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)

@router.post("/rollback/{tx_id}")
def admin_rollback(request: Request, tx_id: int):
    if not is_admin(request):
        return {"ok": False, "detail": "admin only"}
    rollback(tx_id)
    return {"ok": True}
