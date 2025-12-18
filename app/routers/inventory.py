from fastapi import APIRouter
from app.db import get_conn

router = APIRouter(prefix="/api/inventory", tags=["재고"])

@router.get("")
def inventory_list():
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
        WHERE qty > 0
        ORDER BY item_code, location
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
