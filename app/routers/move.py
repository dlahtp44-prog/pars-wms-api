from fastapi import APIRouter, HTTPException
from app.db import get_conn, log_history

router = APIRouter(tags=["재고이동"])

@router.post("/move", summary="재고 이동")
def move(
    warehouse: str,
    from_location: str,
    to_location: str,
    item: str,
    qty: int,
    remark: str = ""
):
    conn = get_conn()
    cur = conn.cursor()

    # 출발지 재고 확인
    cur.execute(
        "SELECT qty FROM inventory WHERE item=? AND location=?",
        (item, from_location)
    )
    row = cur.fetchone()

    if not row or row[0] < qty:
        conn.close()
        raise HTTPException(status_code=400, detail="이동 재고 부족")

    # 출발지 차감
    cur.execute(
        "UPDATE inventory SET qty = qty - ? WHERE item=? AND location=?",
        (qty, item, from_location)
    )

    # 도착지 추가
    cur.execute(
        "SELECT qty FROM inventory WHERE item=? AND location=?",
        (item, to_location)
    )
    row2 = cur.fetchone()

    if row2:
        cur.execute(
            "UPDATE inventory SET qty = qty + ? WHERE item=? AND location=?",
            (qty, item, to_location)
        )
    else:
        cur.execute(
            "INSERT INTO inventory (item, qty, location) VALUES (?, ?, ?)",
            (item, qty, to_location)
        )

    conn.commit()
    conn.close()

    # ✅ 작업이력 기록
    log_history(
        type="이동",
        warehouse=warehouse,
        location=f"{from_location} → {to_location}",
        item=item,
        qty=qty,
        remark=remark
    )

    return {"result": "이동 완료"}
