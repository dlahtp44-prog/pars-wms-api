from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_inventory

router = APIRouter(prefix="/item")
templates = Jinja2Templates(directory="app/templates")

@router.get("/{item_code}")
def item_page(request: Request, item_code: str):
    rows = get_inventory(q=item_code)
    return templates.TemplateResponse("item_page.html", {"request": request, "item_code": item_code, "rows": rows})
