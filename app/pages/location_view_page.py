from fastapi import APIRouter, Query, Request
from fastapi.templating import Jinja2Templates
from app.db import get_location_items

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/location")
def location_view(
    request: Request,
    warehouse: str = "MAIN",
    location: str = Query(...)
):
    rows = get_location_items(warehouse, location)

    return templates.TemplateResponse(
        "location_view.html",
        {
            "request": request,
            "location": location,
            "rows": rows
        }
    )
