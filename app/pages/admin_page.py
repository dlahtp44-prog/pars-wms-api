from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from app.db import admin_password_ok, get_history

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def admin_login(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

@router.post("")
def admin_view(request: Request, password: str = Form(...)):
    if not admin_password_ok(password):
        return templates.TemplateResponse(
            "admin_login.html",
            {"request": request, "error": "비밀번호 오류"}
        )
    rows = get_history()
    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "rows": rows}
    )
