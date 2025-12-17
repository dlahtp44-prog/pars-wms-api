from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_conn

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/inventory-page")
def inventory_page(request: Request, highlight: str = ""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT brand, item, name, lot, spec, location, qty
        FROM inventory
    """)
    rows = cur.fetchall()
    conn.close()

    return templates.TemplateResponse(
        "inventory.html",
        {
            "request": request,
            "rows": rows,
            "highlight": highlight
        }
    )
