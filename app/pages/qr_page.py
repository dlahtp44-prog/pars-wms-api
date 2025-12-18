from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/qr-page")
def qr_page(request: Request):
    return templates.TemplateResponse(
        "qr_page.html",
        {"request": request}
    )
