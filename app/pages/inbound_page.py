from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(
    include_in_schema=False  # ✅ Swagger에서 숨김
)

templates = Jinja2Templates(directory="app/templates")

@router.get(
    "/inbound-page",
    response_class=HTMLResponse  # ✅ HTML 페이지임을 명시
)
def inbound_page(request: Request):
    return templates.TemplateResponse(
        "inbound.html",
        {"request": request}
    )
