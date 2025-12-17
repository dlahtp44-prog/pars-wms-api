from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get(
    "/inbound-page",
    summary="입고 화면",
    description="모바일/PC용 입고 처리 화면"
)
def inbound_page(request: Request):
    return templates.TemplateResponse(
        "inbound.html",
        {"request": request}
    )
