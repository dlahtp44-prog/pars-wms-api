from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/qr", response_class=HTMLResponse)
def qr_page(request: Request):
    return templates.TemplateResponse("qr.html", {"request": request})
