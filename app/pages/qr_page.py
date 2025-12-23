from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/qr-page")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def qr_page(request: Request):
    return templates.TemplateResponse("qr_page.html", {"request": request})
