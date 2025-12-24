from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from app.db import get_history, rollback, admin_password_ok

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def admin_page(request: Request):
    # 로그인 안 되어 있으면 로그인 화면
    if not request.session.get("admin"):
        return templates.TemplateResponse(
            "admin_login.html",
            {"request": request}
        )

    rows = get_history(limit=300)
    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "rows": rows}
    )

@router.post("/login")
def admin_login(request: Request, password: str = Form(...)):
    if admin_password_ok(password):
        request.session["admin"] = True
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse(
        "admin_login.html",
        {"request": request, "error": "비밀번호 오류"}
    )

@router.post("/rollback/{tx_id}")
def admin_rollback(request: Request, tx_id: int):
    if not request.session.get("admin"):
        return RedirectResponse("/admin", status_code=303)
    rollback(tx_id)
    return RedirectResponse("/admin", status_code=303)
