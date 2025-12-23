from fastapi import APIRouter, Query
from app.db import get_conn

router = APIRouter(prefix="/api/location", tags=["Location"])

@router.get("/inventory")
def inventory_by_location(location: str = Query(...)):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            item_code,
            item_name,
            brand,
            spec,
            lot_no,
            qty
        FROM inventory
        WHERE location = ?
        ORDER BY item_code, lot_no
    """, (location,))

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    return {
        "location": location,
        "items": rows
    }
