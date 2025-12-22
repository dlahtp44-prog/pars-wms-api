from fastapi import APIRouter
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/history")

@router.post("/rollback/{history_id}")
def rollback(history_id: int):
    conn = get_conn()
    cur = conn.cursor()

    row = cur.execute(
        "SELECT * FROM history WHERE id=?",
        (history_id,)
    ).fetchone()

    if not row:
        return {"error": "기록 없음"}

    # 반대 작업
    sign = -1 if row["tx_type"] in ("입고", "IN") else 1

    cur.execute("""
        UPDATE inventory
        SET qty = qty + ?
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (
        sign * row["qty"],
        row["warehouse"],
        row["location"],
        row["item_code"],
        row["lot_no"]
    ))

    cur.execute("DELETE FROM history WHERE id=?", (history_id,))
    conn.commit()
    conn.close()

    return {"result": "rollback ok"}

