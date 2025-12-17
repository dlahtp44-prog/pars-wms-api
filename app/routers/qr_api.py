from fastapi import APIRouter, HTTPException
from app.db import get_conn, log_history

router = APIRouter(tags=["QR"])

@router.post(
    "/qr/scan",
    summary="QR 스캔 처리",
    description="QR 데이터로 입고/출고를 자동 처리합니다."
)
def qr_scan(action: str, item: str, qty: int):
    if action not in ["입고", "출고"]:
        raise HTTPException(status_code=400, detail="action은 입고 또는 출고만 가능합니다.")

    conn = get_conn()
    cur = conn.cursor()

    if action == "입고":
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

    else:  # 출고
        cur.execute("SELECT qty FROM inventory WHERE item=?", (item,))
        row = cur.fetchone()

        if not row or row[0] < qty:
            conn.close()
            raise HTTPException(status_code=400, detail="출고 재고 부족")

        cur.execute(
            "UPDATE inventory SET qty = qty - ? WHERE item=?",
            (qty, item)
        )

    conn.commit()
    conn.close()

    log_history(action, item, qty, "QR 처리")

    return {"결과": f"{action} 처리 완료"}
