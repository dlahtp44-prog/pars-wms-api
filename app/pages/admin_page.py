from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_history, rollback

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def admin_page(request: Request):
    rows = get_history()
    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "rows": rows}
    )

@router.post("/rollback/{tx_id}")
def do_rollback(tx_id: int):
    rollback(tx_id)
    return {"ok": True}
