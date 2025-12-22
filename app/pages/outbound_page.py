# app/pages/outbound_page.py
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/outbound-page")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def outbound_page(request: Request):
    return templates.TemplateResponse(
        "outbound.html",
        {"request": request}
    )
