from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_inventory

router = APIRouter(prefix="/inventory-page")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def inventory_page(request: Request, q: str = "", location: str = "", warehouse: str = ""):
    rows = get_inventory(warehouse=warehouse or None, location=location or None, q=q or None)
    return templates.TemplateResponse("inventory.html", {"request": request, "rows": rows, "q": q, "location": location, "warehouse": warehouse})
