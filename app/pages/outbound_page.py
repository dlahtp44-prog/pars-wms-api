from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

router = APIRouter()

@router.get(
    "/outbound-page",
    response_class=HTMLResponse,
    summary="출고 화면"
)
def outbound_page(request: Request):
    return templates.TemplateResponse(
        "outbound.html",
        {"request": request}
    )
