from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_history

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/history-page")
def history_page(request: Request):
    rows = get_history(200)
    return templates.TemplateResponse("history.html", {"request": request, "rows": rows})
