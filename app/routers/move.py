from fastapi import APIRouter, HTTPException
from app.db import get_conn, log_history

router = APIRouter(tags=["재고이동"])

@router.post(
    "/move",
    summary="재고 이동",
    description="품목의 재고를 이동 처리합니다 (수량 차감/유지)."
)
def move(item: str, qty: int, from_loc: str, to_loc: str):
    if qty <= 0:
        raise HTTPException(status_code=400, detail="수량은 1 이상이어야 합니다.")

    conn = get_conn()
    cur = conn.cursor()

    # 현재 재고 확인
    cur.execute(
        "SELECT qty FROM inventory WHERE item=? AND location=?",
        (item, from_loc)
    )
    row = cur.fetchone()

    if not row or row[0] < qty:
        conn.close()
        raise HTTPException(status_code=400, detail="이동할 재고가 부족합니다.")

    # 출발지 차감
    cur.execute(
        "UPDATE inventory SET qty = qty - ? WHERE item=? AND location=?",
        (qty, item, from_loc)
    )

    # 도착지 추가
    cur.execute(
        "SELECT qty FROM inventory WHERE item=? AND location=?",
        (item, to_loc)
    )
    target = cur.fetchone()

    if target:
        cur.execute(
            "UPDATE inventory SET qty = qty + ? WHERE item=? AND location=?",
            (qty, item, to_loc)
        )
    else:
        cur.execute(
            "INSERT INTO inventory (item, qty, location) VALUES (?, ?, ?)",
            (item, qty, to_loc)
        )

    conn.commit()
    conn.close()

    log_history("재고이동", item, qty, f"{from_loc} → {to_loc}")

    return {"결과": "재고 이동 완료"}
