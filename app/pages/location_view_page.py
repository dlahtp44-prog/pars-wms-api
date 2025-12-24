# app/pages/location_view_page.py
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_location_items

router = APIRouter(prefix="/loc")
templates = Jinja2Templates(directory="app/templates")

@router.get("/{loc_code}")
def view(request: Request, loc_code: str):
    rows = get_location_items(loc_code)
    return templates.TemplateResponse("location_view.html", {"request": request, "loc": loc_code, "rows": rows})
