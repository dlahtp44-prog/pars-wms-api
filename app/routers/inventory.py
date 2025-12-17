# app/routers/inventory.py
from fastapi import APIRouter
from app.db import get_conn

router = APIRouter(tags=["재고"])

@router.get("/inventory")
def inventory(warehouse: str | None = None):
    conn = get_conn()
    cur = conn.cursor()

    if warehouse:
        cur.execute("""
            SELECT item, qty, warehouse, zone, rack, level, cell
            FROM inventory WHERE warehouse=?
        """, (warehouse,))
    else:
        cur.execute("""
            SELECT item, qty, warehouse, zone, rack, level, cell
            FROM inventory
        """)

    rows = cur.fetchall()
    conn.close()

    return {
        "재고": [
            {
                "품목": r[0],
                "수량": r[1],
                "창고": r[2],
                "위치": f"{r[3]}-{r[4]}-{r[5]}-{r[6]}"
            } for r in rows
        ]
    }
