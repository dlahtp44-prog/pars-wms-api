from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

router = APIRouter()

@router.get(
    "/",
    response_class=HTMLResponse,
    summary="메인 화면",
    description="모바일/PC 공용 WMS 메인 화면"
)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )
