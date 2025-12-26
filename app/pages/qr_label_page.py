from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/qr/label/location", response_class=HTMLResponse)
def location_label(request: Request):
    return templates.TemplateResponse(
        "qr_label_location.html",
        {"request": request}
    )

@router.get("/qr/label/item", response_class=HTMLResponse)
def item_label(request: Request):
    return templates.TemplateResponse(
        "qr_label_item.html",
        {"request": request}
    )
