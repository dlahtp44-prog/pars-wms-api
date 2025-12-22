# app/pages/move_page.py
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/move-page")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def move_page(request: Request):
    return templates.TemplateResponse(
        "move.html",
        {"request": request}
    )
