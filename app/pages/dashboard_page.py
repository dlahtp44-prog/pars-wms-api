from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import dashboard_summary

router = APIRouter(prefix="/dashboard")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def dashboard(request: Request):
    inbound, outbound, total, negative = dashboard_summary()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "inbound": inbound,
            "outbound": outbound,
            "total": total,
            "negative": negative
        }
    )
