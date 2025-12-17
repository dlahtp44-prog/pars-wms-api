from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_conn

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/inventory-page")
def inventory_page(request: Request, warehouse: str = "", q: str = ""):
    conn = get_conn()
    cur = conn.cursor()

    sql = """
        SELECT warehouse, brand, item, name, lot, spec, location, qty
        FROM inventory
        WHERE 1=1
    """
    params = []

    if warehouse:
        sql += " AND warehouse = ?"
        params.append(warehouse)

    if q:
        sql += """
          AND (
            item LIKE ? OR name LIKE ? OR brand LIKE ?
            OR lot LIKE ? OR location LIKE ?
          )
        """
        like = f"%{q}%"
        params.extend([like, like, like, like, like])

    sql += " ORDER BY warehouse, location, item"
    cur.execute(sql, params)
    rows = cur.fetchall()

    # 창고 목록(필터용)
    cur.execute("SELECT DISTINCT warehouse FROM inventory WHERE warehouse IS NOT NULL AND warehouse != ''")
    warehouses = [r[0] for r in cur.fetchall()]

    conn.close()

    return templates.TemplateResponse(
        "inventory.html",
        {
            "request": request,
            "rows": rows,
            "warehouses": warehouses,
            "warehouse": warehouse,
            "q": q
        }
    )
