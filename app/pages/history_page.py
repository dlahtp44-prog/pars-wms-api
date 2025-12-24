from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_history

router = APIRouter(prefix="/history-page")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def history_page(request: Request):
    rows = get_history(limit=500)
    return templates.TemplateResponse("history.html", {"request": request, "rows": rows})
