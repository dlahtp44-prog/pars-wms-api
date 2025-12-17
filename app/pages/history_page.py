# app/pages/history_page.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.db import get_conn

router = APIRouter(prefix="/history-page", tags=["Page"], include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
def history_page(request: Request):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT type, item, qty, remark, created_at
        FROM history
        ORDER BY id DESC
    """)
    rows = cur.fetchall()

    conn.close()

    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "rows": rows
        }
    )
