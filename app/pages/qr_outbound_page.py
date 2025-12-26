from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/qr/outbound", response_class=HTMLResponse)
def qr_outbound_page(request: Request):
    return templates.TemplateResponse(
        "qr_outbound.html",
        {"request": request}
    )
