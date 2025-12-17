from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/qr-label")
def qr_label_page(request: Request):
    return templates.TemplateResponse(
        "qr_label.html",
        {"request": request}
    )

