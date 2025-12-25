from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.db import get_inventory_by_location

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/location-view", response_class=HTMLResponse)
def location_view(
    request: Request,
    location: str = Query(...),
    warehouse: str = Query("MAIN")
):
    rows = get_inventory_by_location(warehouse, location)
    return templates.TemplateResponse(
        "location_view.html",
        {
            "request": request,
            "location": location,
            "warehouse": warehouse,
            "rows": rows
        }
    )
