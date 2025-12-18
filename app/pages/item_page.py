from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_conn

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/item/{item_code}")
def item_detail(request: Request, item_code: str):
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            location_name,
            lot_no,
            spec,
            location,
            qty
        FROM inventory
        WHERE item_code = ?
    """, (item_code,)).fetchall()
    conn.close()

    return templates.TemplateResponse(
        "item.html",
        {
            "request": request,
            "item_code": item_code,
            "rows": rows
        }
    )
