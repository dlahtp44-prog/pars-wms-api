from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_conn

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/inventory-page")
def inventory_page(request: Request):
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            location_name,
            brand,
            item_code,
            item_name,
            lot_no,
            spec,
            location,
            qty
        FROM inventory
        ORDER BY item_code
    """).fetchall()
    conn.close()

    return templates.TemplateResponse(
        "inventory_page.html",
        {
            "request": request,
            "rows": rows
        }
    )
