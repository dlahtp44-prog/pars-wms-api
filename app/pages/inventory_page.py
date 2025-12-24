from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app import db

# 메인 앱에서 등록할 수 있도록 router 객체를 생성합니다.
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/inventory-page", response_class=HTMLResponse)
async def inventory_page(request: Request, q: str = None):
    # db.py의 검색 기능이 포함된 재고 조회 함수 호출
    rows = db.get_inventory(q=q)
    
    return templates.TemplateResponse("inventory_page.html", {
        "request": request,
        "rows": rows,
        "q": q or ""
    })
