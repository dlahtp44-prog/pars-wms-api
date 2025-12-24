from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import dashboard_summary

router = APIRouter(prefix="/dashboard")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def page(request: Request):
    s = dashboard_summary()
    # "s": s 로 넘겨야 templates에서 s.inbound_today 로 접근 가능합니다.
    return templates.TemplateResponse("dashboard.html", {"request": request, "s": s})
