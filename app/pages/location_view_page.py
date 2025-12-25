from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_location_items

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/location/{loc}")
def location_view(request: Request, loc: str):
    items = get_location_items(loc)
    return templates.TemplateResponse(
        "location_view.html",
        {"request": request, "loc": loc, "items": items}
    )
