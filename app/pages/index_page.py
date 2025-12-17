from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

templates = Jinja2Templates(directory=TEMPLATE_DIR)

router = APIRouter()

@router.get(
    "/",
    response_class=HTMLResponse,
    summary="메인 화면",
    description="PARS WMS 메인 대시보드 (모바일·PC 공용)"
)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )
