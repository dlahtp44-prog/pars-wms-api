from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/inbound-page")
def inbound_page(request: Request):
    return templates.TemplateResponse(
        "inbound.html",
        {"request": request}
    )
