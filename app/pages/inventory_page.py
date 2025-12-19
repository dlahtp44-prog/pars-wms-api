from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_conn

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/inventory-page")
def inventory_page(
    request: Request,
    location: str = "",
    item_code: str = ""
):
    conn = get_conn()
    cur = conn.cursor()

    sql = """
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
        WHERE 1=1
    """
    params = []

    if location:
        sql += " AND location LIKE ?"
        params.append(f"%{location}%")

    if item_code:
        sql += " AND item_code LIKE ?"
        params.append(f"%{item_code}%")

    rows = cur.execute(sql, params).fetchall()
    conn.close()

    return templates.TemplateResponse(
        "inventory.html",
        {
            "request": request,
            "rows": rows
        }
    )
