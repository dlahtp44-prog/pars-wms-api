from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.db import get_history, admin_password_ok
from app.auth import require_admin, is_admin

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def admin_home(request: Request):
    if not is_admin(request):
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": ""})
    rows = get_history(limit=300)
    return templates.TemplateResponse("admin.html", {"request": request, "rows": rows})

@router.post("/login")
def admin_login(request: Request, password: str = Form(...)):
    if admin_password_ok(password):
        request.session["is_admin"] = True
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": "비밀번호가 틀렸습니다."})

@router.get("/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin", status_code=303)
