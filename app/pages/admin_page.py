from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_qr_errors, mark_qr_errors_checked

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")

@router.get("/qr-dashboard")
def qr_dashboard(request: Request):
    rows = get_qr_errors(200)
    mark_qr_errors_checked()  # 접속 시 자동 초기화

    return templates.TemplateResponse(
        "admin_qr_dashboard.html",
        {"request": request, "rows": rows}
    )
