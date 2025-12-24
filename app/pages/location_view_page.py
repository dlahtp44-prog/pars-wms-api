from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_location_items

router = APIRouter(prefix="/loc")
templates = Jinja2Templates(directory="app/templates")

@router.get("/{location}")
def loc_view(request: Request, location: str, warehouse: str = "MAIN"):
    rows = get_location_items(location=location, warehouse=warehouse)
    return templates.TemplateResponse("location_view.html", {"request": request, "rows": rows, "location": location, "warehouse": warehouse})
