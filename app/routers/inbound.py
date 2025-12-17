from fastapi import APIRouter
from app.db import get_conn, log_history

router = APIRouter(tags=["입고"])

@router.post("/inbound", summary="입고 처리")
def inbound(
    warehouse: str,
    location: str,
    item: str,
    qty: int,
    remark: str = ""
):
    conn = get_conn()
    cur = conn.cursor()

    # 재고 존재 확인
    cur.execute(
        "SELECT qty FROM inventory WHERE item=? AND location=?",
        (item, location)
    )
    row = cur.fetchone()

    if row:
        cur.execute(
            "UPDATE inventory SET qty = qty + ? WHERE item=? AND location=?",
            (qty, item, location)
        )
    else:
        cur.execute(
            "INSERT INTO inventory (item, qty, location) VALUES (?, ?, ?)",
            (item, qty, location)
        )

    conn.commit()
    conn.close()

    # ✅ 작업이력 기록
    log_history(
        type="입고",
        warehouse=warehouse,
        location=location,
        item=item,
        qty=qty,
        remark=remark
    )

    return {"result": "입고 완료"}
