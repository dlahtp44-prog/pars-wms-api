from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.db import get_inventory, dashboard_summary

router = APIRouter(prefix="/dashboard")
templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse)
def dashboard(request: Request):
    rows = get_inventory()
    s = dashboard_summary()
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "rows": rows, "s": s}
    )
