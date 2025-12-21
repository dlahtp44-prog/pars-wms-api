from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_conn

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/item/{item_code}")
def item_page(request: Request, item_code: str):
    conn = get_conn()
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT warehouse, location, brand, item_code, item_name, lot_no, spec, qty
        FROM inventory
        WHERE item_code = ?
        ORDER BY warehouse, location, lot_no
    """, (item_code,)).fetchall()
    conn.close()

    return templates.TemplateResponse(
        "item.html",
        {"request": request, "item_code": item_code, "rows": [dict(r) for r in rows]}
    )
