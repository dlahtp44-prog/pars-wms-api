# app/routers/inbound.py
from fastapi import APIRouter
from app.db import get_conn, log_history

router = APIRouter(tags=["입고"])

@router.post("/inbound")
def inbound(
    item: str,
    qty: int,
    warehouse: str,
    zone: str,
    rack: str,
    level: str,
    cell: str,
    remark: str = ""
):
    location = f"{zone}-{rack}-{level}-{cell}"

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT qty FROM inventory WHERE item=?", (item,))
    row = cur.fetchone()

    if row:
        cur.execute("""
            UPDATE inventory
            SET qty = qty + ?,
                warehouse=?,
                zone=?, rack=?, level=?, cell=?
            WHERE item=?
        """, (qty, warehouse, zone, rack, level, cell, item))
    else:
        cur.execute("""
            INSERT INTO inventory
            (item, qty, warehouse, zone, rack, level, cell)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (item, qty, warehouse, zone, rack, level, cell))

    conn.commit()
    conn.close()

    log_history("입고", item, qty, warehouse, location, remark)

    return {"result": "입고 완료", "location": location}
