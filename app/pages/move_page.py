from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# =========================
# Router 설정
# =========================
router = APIRouter(
    tags=["Page"],
    include_in_schema=False  # Swagger 숨김 (화면 전용)
)

# =========================
# Template 설정
# =========================
templates = Jinja2Templates(directory="app/templates")

# =========================
# 재고 이동 화면
# URL: /move-page
# =========================
@router.get("/move-page", response_class=HTMLResponse)
def move_page(request: Request):
    """
    재고 이동 화면 (모바일/PC 공용)
    """
    return templates.TemplateResponse(
        "move.html",
        {
            "request": request,
            "title": "재고 이동"
        }
    )
