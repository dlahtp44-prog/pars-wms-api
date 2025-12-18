from fastapi import APIRouter, Query
from app.db import get_conn

router = APIRouter(prefix="/api", tags=["QR"])

@router.get("/qr-search")
def qr_search(q: str = Query(...)):
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
        WHERE
            item_code LIKE ?
            OR lot_no LIKE ?
    """, (f"%{q}%", f"%{q}%")).fetchall()
    conn.close()

    return [dict(r) for r in rows]
