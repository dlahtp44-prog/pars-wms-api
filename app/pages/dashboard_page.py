from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_inventory

router = APIRouter(prefix="/dashboard")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def dashboard(request: Request):
    rows = get_inventory()
    total = sum(r["qty"] for r in rows)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "rows": rows, "total": total}
    )
