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

    query = """
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
        query += " AND location LIKE ?"
        params.append(f"%{location}%")

    if item_code:
        query += " AND item_code LIKE ?"
        params.append(f"%{item_code}%")

    rows = cur.execute(query, params).fetchall()
    conn.close()

    return templates.TemplateResponse(
        "inventory_page.html",
        {
            "request": request,
            "rows": rows,
            "location": location,
            "item_code": item_code
        }
    )
