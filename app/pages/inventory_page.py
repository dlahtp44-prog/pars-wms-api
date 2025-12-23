from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_inventory

router = APIRouter(prefix="/inventory-page")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def inventory_page(request: Request, q: str = "", warehouse: str = "", location: str = ""):
    rows = get_inventory(
        warehouse=warehouse if warehouse else None,
        location=location if location else None,
        q=q
    )
    return templates.TemplateResponse("inventory_page.html", {
        "request": request,
        "rows": rows,
        "q": q,
        "warehouse": warehouse,
        "location": location
    })
