from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_inventory

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
def index(request: Request):
    rows = get_inventory()
    return templates.TemplateResponse("index.html", {"request": request, "rows": rows})
