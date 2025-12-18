from fastapi import APIRouter, Query
from app.db import get_conn

router = APIRouter(prefix="/api/inventory", tags=["재고"])

@router.get("")
def inventory_search(
    location: str | None = Query(None),
    item_code: str | None = Query(None)
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
        sql += " AND location = ?"
        params.append(location)

    if item_code:
        sql += " AND item_code = ?"
        params.append(item_code)

    rows = cur.execute(sql, params).fetchall()
    conn.close()

    return [dict(r) for r in rows]
