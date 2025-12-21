from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_history

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/admin-page")
def admin_page(request: Request):
    rows = get_history(300)
    return templates.TemplateResponse("admin.html", {"request": request, "rows": rows})
