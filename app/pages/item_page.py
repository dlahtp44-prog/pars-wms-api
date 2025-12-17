
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_conn

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/item/{item}")
def item_page(request: Request, item: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT warehouse, brand, item, name, lot, spec, location, qty
        FROM inventory
        WHERE item = ?
    """, (item,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return {"error": "품목 없음"}

    return templates.TemplateResponse(
        "item_detail.html",
        {"request": request, "r": row}
    )
