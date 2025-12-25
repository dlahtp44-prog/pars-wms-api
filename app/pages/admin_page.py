from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")

ADMIN_PASSWORD = "admin1234"  # ✅ 임시 비밀번호

@router.get("")
def admin_page(request: Request):
    if not request.session.get("admin"):
        return templates.TemplateResponse("admin_login.html", {"request": request})
    return templates.TemplateResponse("admin.html", {"request": request})

@router.post("/login")
def admin_login(request: Request, password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        request.session["admin"] = True
        return RedirectResponse("/admin", status_code=303)
    return RedirectResponse("/admin", status_code=303)

@router.get("/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)
