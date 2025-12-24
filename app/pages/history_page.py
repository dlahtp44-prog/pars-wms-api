from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_history

router = APIRouter(prefix="/history-page")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def page(request: Request):
    rows = get_history()
    return templates.TemplateResponse("history.html", {"request": request, "rows": rows})
