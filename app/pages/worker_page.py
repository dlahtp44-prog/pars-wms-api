from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/worker", summary="작업자 메인 화면")
def worker_page(request: Request):
    return templates.TemplateResponse(
        "worker.html",
        {"request": request}
    )

