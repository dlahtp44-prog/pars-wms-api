
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/worker", tags=["작업자"])
templates = Jinja2Templates(directory="app/templates")

@router.get(
    "",
    response_class=HTMLResponse,
    summary="작업자 입·출고 화면",
    description="모바일/PDA 작업자 전용 입고·출고 화면"
)
def worker_home(request: Request):
    return templates.TemplateResponse(
        "worker.html",
        {"request": request}
    )
