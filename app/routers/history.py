from fastapi import APIRouter
from app.db import get_history, rollback

router = APIRouter(prefix="/api/history", tags=["이력"])

@router.get("")
def history_list(limit: int = 300):
    return get_history(limit=limit)

@router.post("/rollback/{history_id}")
def history_rollback(history_id: int):
    return rollback(history_id)


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

