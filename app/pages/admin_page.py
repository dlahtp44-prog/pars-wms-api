from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_history

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def admin(request: Request):
    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "rows": get_history()}
    )
