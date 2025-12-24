from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_inventory

router = APIRouter(prefix="/inventory-page")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def page(request: Request, q: str = ""):
    rows = get_inventory(q=q)
    return templates.TemplateResponse("inventory.html", {"request": request, "rows": rows, "q": q})
