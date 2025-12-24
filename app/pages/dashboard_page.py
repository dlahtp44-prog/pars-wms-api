from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import dashboard_summary

router = APIRouter(prefix="/dashboard")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def page(request: Request):
    s = dashboard_summary()
    # **s를 {"s": s}로 변경하여 템플릿의 변수 구조와 맞춥니다.
    return templates.TemplateResponse("dashboard.html", {"request": request, "s": s})
