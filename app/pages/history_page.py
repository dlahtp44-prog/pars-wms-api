from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_conn

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/history-page")
def history_page(request: Request):
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT action, item, qty, created_at
            FROM history
            ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
    except Exception as e:
        rows = []
    finally:
        conn.close()

    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "rows": rows
        }
    )
