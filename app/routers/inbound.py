from fastapi import APIRouter
from app.db import get_conn, log_history

router = APIRouter(tags=["입고"])

@router.post("/inbound", summary="입고 처리")
def inbound(item: str, qty: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT qty FROM inventory WHERE item=?", (item,))
    row = cur.fetchone()

    if row:
        cur.execute(
            "UPDATE inventory SET qty = qty + ? WHERE item=?",
            (qty, item)
        )
    else:
        cur.execute(
            "INSERT INTO inventory (item, qty) VALUES (?, ?)",
            (item, qty)
        )

    conn.commit()
    conn.close()

    log_history("입고", item, qty)
    return {"결과": "입고 완료"}
