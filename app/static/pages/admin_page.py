from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import dashboard_summary, get_history

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def admin_page(request: Request):
    summary = dashboard_summary()
    hist = get_history(30)
    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "summary": summary, "hist": hist}
    )
