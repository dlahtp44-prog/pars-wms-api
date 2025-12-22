# app/pages/admin_page.py
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from app.db import get_history, rollback

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")


# 관리자 페이지
@router.get("")
def admin_page(request: Request):
    rows = get_history()
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "rows": rows
        }
    )


# 롤백 처리
@router.post("/rollback/{tx_id}")
def admin_rollback(tx_id: int):
    rollback(tx_id)
    return {"ok": True}
