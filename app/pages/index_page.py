from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import dashboard_summary

router = APIRouter(prefix="")
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
def index(request: Request):
    s = dashboard_summary()
    return templates.TemplateResponse("index.html", {"request": request, **s})
