from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import (
    get_inventory,
    get_dashboard_summary,
    get_lot_summary
)

router = APIRouter(prefix="/dashboard")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def dashboard(request: Request):
    rows = get_inventory()
    summary = get_dashboard_summary()
    lot_rows = get_lot_summary()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "rows": rows,
            "summary": summary,
            "lot_rows": lot_rows
        }
    )
