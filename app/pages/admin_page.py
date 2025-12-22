from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import os
from app.db import get_history

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def admin_login(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

@router.post("/login")
def admin_login_post(password: str = Form(...)):
    if password == os.getenv("ADMIN_PASSWORD", "1234"):
        resp = RedirectResponse("/admin/dashboard", status_code=303)
        resp.set_cookie("admin", "1", httponly=True)
        return resp
    return {"error": "비밀번호 오류"}

@router.get("/dashboard")
def admin_dashboard(request: Request):
    if request.cookies.get("admin") != "1":
        return RedirectResponse("/admin", status_code=303)

    rows = get_history()
    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "rows": rows}
    )
