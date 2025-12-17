from fastapi import APIRouter, HTTPException
from app.db import get_conn, log_history

router = APIRouter(tags=["출고"])

@router.post("/outbound")
def outbound(item: str, qty: int, remark: str = ""):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT qty, warehouse, location FROM inventory WHERE item=?
    """, (item,))
    row = cur.fetchone()

    if not row or row[0] < qty:
        raise HTTPException(status_code=400, detail="재고 부족")

    cur.execute(
        "UPDATE inventory SET qty = qty - ? WHERE item=?",
        (qty, item)
    )

    conn.commit()
    conn.close()

    log_history("출고", item, -qty, row[1], row[2], remark)
    return {"result": "출고 완료"}
