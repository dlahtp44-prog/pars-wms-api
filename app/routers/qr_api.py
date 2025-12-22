from fastapi import APIRouter, Query
from app.db import get_conn

router = APIRouter(prefix="/api", tags=["QR"])

@router.get("/qr-search")
def qr_search(q: str = Query(..., min_length=1)):
    """
    q로 inventory에서 item_code / lot_no / location 등 검색
    """
    conn = get_conn()
    cur = conn.cursor()

    kw = f"%{q}%"
    cur.execute("""
        SELECT
            COALESCE(warehouse,'') as location_name,
            item_code,
            lot_no,
            location,
            SUM(qty) as qty
        FROM inventory
        WHERE
          item_code LIKE ?
          OR lot_no LIKE ?
          OR location LIKE ?
          OR item_name LIKE ?
        GROUP BY warehouse, location, item_code, lot_no
        ORDER BY item_code
        LIMIT 200
    """, (kw, kw, kw, kw))

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
