from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_conn

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/history-page")
def history_page(request: Request):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            location_name,
            brand,
            item,
            name,
            lot,
            spec,
            location,
            qty
        FROM history
        ORDER BY created_at DESC
    """)

    rows = [
        {
            "location_name": r[0],
            "brand": r[1],
            "item": r[2],
            "name": r[3],
            "lot": r[4],
            "spec": r[5],
            "location": r[6],
            "qty": r[7],
        }
        for r in cur.fetchall()
    ]

    conn.close()

    return templates.TemplateResponse(
        "inventory.html",
        {
            "request": request,
            "rows": rows,
            "title": "작업 이력"
        }
    )
