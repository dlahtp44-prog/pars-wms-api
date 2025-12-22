from fastapi import APIRouter, Query
from app.db import get_conn

router = APIRouter(prefix="/api", tags=["QR"])

@router.get("/qr-search")
def qr_search(q: str = Query(...)):
    conn = get_conn()
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT warehouse, location, brand, item_code, item_name, lot_no, spec, SUM(qty) as qty
        FROM inventory
        WHERE item_code LIKE ? OR lot_no LIKE ?
        GROUP BY warehouse, location, item_code, lot_no
        ORDER BY item_code
    """, (f"%{q}%", f"%{q}%")).fetchall()
    conn.close()
    return [dict(r) for r in rows]
