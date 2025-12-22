from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/qr-page")
templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse)
def qr_page(request: Request):
    return templates.TemplateResponse("qr.html", {"request": request})
