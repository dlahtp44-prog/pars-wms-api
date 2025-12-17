from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get(
    "/inventory-page",
    response_class=HTMLResponse,
    summary="재고 조회 화면"
)
def inventory_page(request: Request):
    return templates.TemplateResponse(
        "inventory.html",
        {"request": request}
    )
