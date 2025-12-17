from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

router = APIRouter()

@router.get(
    "/inbound-page",
    response_class=HTMLResponse,
    summary="입고 화면"
)
def inbound_page(request: Request):
    return templates.TemplateResponse(
        "inbound.html",
        {"request": request}
    )
