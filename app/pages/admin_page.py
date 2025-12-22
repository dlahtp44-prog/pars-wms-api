from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from app.db import get_history, rollback

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")


@router.get("")
def admin_page(request: Request):
    rows = get_history()
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "rows": rows
        }
    )


@router.post("/rollback/{history_id}")
def admin_rollback(history_id: int):
    rollback(history_id)
    return {"result": "OK"}
