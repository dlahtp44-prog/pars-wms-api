# app/pages/inventory_page.py
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_inventory

router = APIRouter(prefix="/inventory-page")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def inventory_page(request: Request):
    rows = get_inventory()
    return templates.TemplateResponse(
        "inventory.html",
        {"request": request, "rows": rows}
    )
