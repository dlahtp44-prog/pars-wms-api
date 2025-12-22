from fastapi import APIRouter
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/history")

@router.post("/rollback/{id}")
def rollback(tx_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM history WHERE id=?", (tx_id,))
    row = cur.fetchone()
    if not row:
        return {"error": "없음"}

    qty = -row["qty"]
    cur.execute("""
        UPDATE inventory
        SET qty = qty + ?
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, row["warehouse"], row["location"], row["item_code"], row["lot_no"]))

    log_history("ROLLBACK", row["warehouse"], row["location"],
                row["item_code"], row["lot_no"], qty, "복구")

    conn.commit()
    conn.close()
    return {"result": "OK"}
