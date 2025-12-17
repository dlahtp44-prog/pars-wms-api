from fastapi import APIRouter
from app.db import get_conn, log_history

router = APIRouter(tags=["출고"])

@router.post("/outbound")
def outbound(item: str, qty: int, remark: str = ""):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "UPDATE inventory SET qty = qty - ? WHERE item = ?",
        (qty, item)
    )

    conn.commit()
    conn.close()

    # ✅ 작업이력 기록
    log_history("출고", item, qty, remark)

    return {"result": "출고 완료"}
