# app/pages/location_view_page.py
from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates
from app.db import get_location_items

router = APIRouter(prefix="/location")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def location_view(
    request: Request,
    warehouse: str = Query("MAIN"),
    location: str = Query(...)
):
    items = get_location_items(warehouse, location)
    return templates.TemplateResponse(
        "location_view.html",
        {"request": request, "warehouse": warehouse, "location": location, "items": items}
    )
