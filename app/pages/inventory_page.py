from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app import db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/inventory-page", response_class=HTMLResponse)
async def inventory_page(request: Request, q: str = None):
    # db.py에서 검색 기능이 포함된 데이터를 가져옵니다.
    rows = db.get_inventory(q=q)
    
    return templates.TemplateResponse("inventory_page.html", {
        "request": request,
        "rows": rows,
        "q": q or ""
    })
