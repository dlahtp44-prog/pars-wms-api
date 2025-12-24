from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_location_items

router = APIRouter(prefix="/location")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def page(request: Request, warehouse: str = "MAIN", location: str = ""):
    rows = get_location_items(location=location, warehouse=warehouse) if location else []
    return templates.TemplateResponse(
        "location_view.html",
        {"request": request, "warehouse": warehouse, "location": location, "rows": rows}
    )
