# app/pages/dashboard_page.py
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import dashboard_summary, get_inventory

router = APIRouter(prefix="/dashboard")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def dashboard(request: Request):
    s = dashboard_summary()
    rows = get_inventory("")[:50]
    return templates.TemplateResponse("dashboard.html", {"request": request, "s": s, "rows": rows})
