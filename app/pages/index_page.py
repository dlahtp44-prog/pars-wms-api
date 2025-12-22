# pages/index_page.py
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_history

router = APIRouter()
templates = Jinja2Templates("app/templates")

@router.get("/")
def index(request: Request):
    qr_error_cnt = sum(1 for h in get_history() if h["tx_type"] == "QR_ERROR")
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "qr_error_cnt": qr_error_cnt}
    )
