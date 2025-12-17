from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
import sqlite3

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

DB_PATH = "wms.db"


@router.get(
    "/history-page",
    summary="작업 이력 화면",
    description="입고, 출고, 이동 작업 이력을 조회하는 화면",
    include_in_schema=False
)
def history_page(request: Request):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT action, item_code, qty, location, created_at
        FROM history
        ORDER BY id DESC
        LIMIT 100
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
