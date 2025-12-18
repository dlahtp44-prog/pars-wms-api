from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import RedirectResponse
from app.db import get_conn, log_history

router = APIRouter(prefix="/api", tags=["이동"])

@router.post("/move")
def move(
    item_code: str = Form(...),
    qty: int = Form(...),
    from_location: str = Form(...),
    to_location: str = Form(...)
):
    conn = get_conn()
    cur = conn.cursor()

    # 1️⃣ 출발지 재고 확인
    cur.execute(
        "SELECT qty FROM inventory WHERE item_code=? AND location=?",
        (item_code, from_location)
    )
    row = cur.fetchone()

    if not row or row["qty"] < qty:
        conn.close()
        raise HTTPException(status_code=400, detail="이동 재고 부족")

    # 2️⃣ 출발지 차감
    cur.execute(
        "UPDATE inventory SET qty = qty - ? WHERE item_code=? AND location=?",
        (qty, item_code, from_location)
    )

    # 3️⃣ 도착지 추가 (있으면 UPDATE, 없으면 INSERT)
    cur.execute(
        "SELECT qty FROM inventory WHERE item_code=? AND location=?",
        (item_code, to_location)
    )
    row2 = cur.fetchone()

    if row2:
        cur.execute(
            "UPDATE inventory SET qty = qty + ? WHERE item_code=? AND location=?",
            (qty, item_code, to_location)
        )
    else:
        cur.execute(
            "INSERT INTO inventory (item_code, location, qty) VALUES (?, ?, ?)",
            (item_code, to_location, qty)
        )

    # 4️⃣ 작업 이력 기록
    log_history(
        tx_type="이동",
        item_code=item_code,
        qty=qty,
        location=f"{from_location} → {to_location}"
    )

    conn.commit()
    conn.close()

    # 5️⃣ 작업자 메인으로 복귀
    return RedirectResponse(url="/worker", status_code=303)
