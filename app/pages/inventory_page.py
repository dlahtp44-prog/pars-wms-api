from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app import db

# [중요] 메인 앱에서 참조할 router 객체를 반드시 정의해야 합니다.
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/inventory-page", response_class=HTMLResponse)
async def inventory_page(request: Request, q: str = None):
    # db.py에서 수정한 검색어(q) 지원 함수 호출
    rows = db.get_inventory(q=q)
    
    return templates.TemplateResponse("inventory_page.html", {
        "request": request,
        "rows": rows,
        "q": q or ""
    })
