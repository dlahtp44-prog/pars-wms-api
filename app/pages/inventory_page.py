from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_conn

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/inventory-page")
def inventory_page(request: Request, location: str = "", item_code: str = ""):
    conn = get_conn()
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT
            location_name, brand, item_code, item_name,
            lot_no, spec, location, qty
        FROM inventory
        WHERE (? = '' OR location = ?)
          AND (? = '' OR item_code = ?)
    """, (location, location, item_code, item_code)).fetchall()

    conn.close()

    return templates.TemplateResponse(
        "inventory.html",
        {
            "request": request,
            "rows": rows
        }
    )
