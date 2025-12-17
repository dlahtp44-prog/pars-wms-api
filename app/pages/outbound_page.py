from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/outbound-page")
def outbound_page(request: Request):
    return templates.TemplateResponse("outbound.html", {"request": request})
