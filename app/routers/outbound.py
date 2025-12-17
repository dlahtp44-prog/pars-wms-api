from fastapi import APIRouter, HTTPException
from app.db import get_conn, log_history

router = APIRouter(tags=["출고"])

@router.post("/outbound", summary="출고 처리")
def outbound(
    warehouse: str,
    location: str,
    item: str,
    qty: int,
    remark: str = ""
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT qty FROM inventory WHERE item=? AND location=?",
        (item, location)
    )
    row = cur.fetchone()

    if not row or row[0] < qty:
        conn.close()
        raise HTTPException(status_code=400, detail="재고 부족")

    cur.execute(
        "UPDATE inventory SET qty = qty - ? WHERE item=? AND location=?",
        (qty, item, location)
    )

    conn.commit()
    conn.close()

    # ✅ 작업이력 기록
    log_history(
        type="출고",
        warehouse=warehouse,
        location=location,
        item=item,
        qty=qty,
        remark=remark
    )

    return {"result": "출고 완료"}
