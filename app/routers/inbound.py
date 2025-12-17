from fastapi import APIRouter
from app.db import get_conn, log_history

router = APIRouter(tags=["입고"])

@router.post("/inbound", summary="입고 처리")
def inbound(item: str, qty: int, location: str, remark: str = ""):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT qty FROM inventory WHERE item = ?", (item,))
    row = cur.fetchone()

    if row:
        cur.execute(
            """
            UPDATE inventory
            SET qty = qty + ?, location = ?
            WHERE item = ?
            """,
            (qty, location, item)
        )
    else:
        cur.execute(
            """
            INSERT INTO inventory (item, qty, location)
            VALUES (?, ?, ?)
            """,
            (item, qty, location)
        )

    conn.commit()
    conn.close()

    log_history("입고", item, qty, location, remark)

    return {
        "result": "입고 완료",
        "item": item,
        "qty": qty,
        "location": location
    }
