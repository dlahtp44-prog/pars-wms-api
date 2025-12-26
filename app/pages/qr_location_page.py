# ==================================================
# QR LOCATION INVENTORY PAGE
# ==================================================
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()

@router.get("/qr/location", response_class=HTMLResponse)
def qr_location_page(request: Request):
    return templates.TemplateResponse(
        "qr_location.html",
        {"request": request}
    )
