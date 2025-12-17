from fastapi import APIRouter, HTTPException
from app.db import get_conn, log_history

router = APIRouter(tags=["입고"])

@router.post(
    "/inbound",
    summary="입고 처리",
    description="품목을 입고 처리하여 재고를 증가시키고 작업 이력을 저장합니다."
)
def inbound(item: str, qty: int):
    # ✅ 유효성 검사
    if qty <= 0:
        raise HTTPException(status_code=400, detail="수량은 1 이상이어야 합니다.")

    try:
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

        # 작업 이력 저장
        log_history("입고", item, qty)

        return {"결과": "입고 완료", "품목": item, "수량": qty}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
