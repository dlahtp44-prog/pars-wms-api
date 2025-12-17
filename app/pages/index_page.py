from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get(
    "/",
    response_class=HTMLResponse,
    summary="메인 화면",
    description="PARS WMS 메인 대시보드"
)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )
