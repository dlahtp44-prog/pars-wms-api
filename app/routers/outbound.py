from fastapi import APIRouter, HTTPException
from app.db import get_conn, log_history

router = APIRouter(tags=["출고"])

@router.post("/outbound", summary="출고 처리")
def outbound(item: str, qty: int, remark: str = "출고"):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT qty FROM inventory WHERE item=?", (item,))
    row = cur.fetchone()

    if not row or row[0] < qty:
        conn.close()
        raise HTTPException(status_code=400, detail="재고 부족")

    cur.execute(
        "UPDATE inventory SET qty = qty - ? WHERE item=?",
        (qty, item)
    )

    conn.commit()
    conn.close()

    # ✅ 작업 이력 기록
    log_history("출고", item, qty, remark)

    return {"결과": "출고 완료"}
