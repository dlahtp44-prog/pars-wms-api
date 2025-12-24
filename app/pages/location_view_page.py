from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates
from app.db import get_inventory

router = APIRouter(prefix="/location")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def location_view(request: Request, location: str):
    rows = get_inventory(location=location)
    return templates.TemplateResponse(
        "location_view.html",
        {"request": request, "rows": rows, "location": location}
    )
