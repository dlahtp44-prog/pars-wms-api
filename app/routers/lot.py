from fastapi import APIRouter
from app.db import get_conn

router = APIRouter(prefix="/api/lot")

@router.get("")
def lots():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT item_code, lot_no, shade, SUM(qty) qty
        FROM inventory
        GROUP BY item_code, lot_no, shade
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
