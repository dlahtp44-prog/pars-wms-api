from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_inventory, dashboard_summary

router = APIRouter(prefix="/dashboard")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def dashboard_page(request: Request):
    rows = get_inventory()
    summary = dashboard_summary()
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "rows": rows, "summary": summary}
    )
