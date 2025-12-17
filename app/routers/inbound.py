from fastapi import APIRouter
from app.db import get_conn, log_history

router = APIRouter(tags=["입고"])

@router.post("/inbound")
def inbound(
    item: str,
    brand: str,
    name: str,
    lot: str,
    spec: str,
    warehouse: str,
    location: str,
    qty: int,
    remark: str = ""
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT qty FROM inventory WHERE item=?", (item,))
    row = cur.fetchone()

    if row:
        cur.execute("""
            UPDATE inventory
            SET qty = qty + ?, warehouse=?, location=?
            WHERE item=?
        """, (qty, warehouse, location, item))
    else:
        cur.execute("""
            INSERT INTO inventory
            (item, brand, name, lot, spec, warehouse, location, qty)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (item, brand, name, lot, spec, warehouse, location, qty))

    conn.commit()
    conn.close()

    log_history("입고", item, qty, warehouse, location, remark)
    return {"result": "입고 완료"}
