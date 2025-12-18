from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import RedirectResponse
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/move", tags=["이동"])

@router.post("")
def move_inventory(
    item_code: str = Form(...),
    lot_no: str = Form(...),
    qty: int = Form(...),
    from_location: str = Form(...),
    to_location: str = Form(...)
):
    conn = get_conn()
    cur = conn.cursor()

    # =========================
    # 1️⃣ 출발지 재고 확인
    # =========================
    row = cur.execute("""
        SELECT
            location_name,
            brand,
            item_name,
            spec,
            qty
        FROM inventory
        WHERE item_code = ?
          AND lot_no = ?
          AND location = ?
    """, (item_code, lot_no, from_location)).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=400, detail="출발지 재고 없음")

    if row["qty"] < qty:
        conn.close()
        raise HTTPException(status_code=400, detail="이동 수량이 재고보다 많습니다")

    location_name = row["location_name"]
    brand = row["brand"]
    item_name = row["item_name"]
    spec = row["spec"]

    # =========================
    # 2️⃣ 출발지 재고 차감
    # =========================
    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?
        WHERE item_code = ?
          AND lot_no = ?
          AND location = ?
    """, (qty, item_code, lot_no, from_location))

    # =========================
    # 3️⃣ 도착지 재고 추가 (없으면 생성)
    # =========================
    cur.execute("""
        INSERT INTO inventory (
            location_name, brand, item_code, item_name,
            lot_no, spec, location, qty
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(item_code, lot_no, location)
        DO UPDATE SET qty = qty + ?
    """, (
        location_name, brand, item_code, item_name,
        lot_no, spec, to_location, qty, qty
    ))

    # =========================
    # 4️⃣ 작업이력 기록
    # =========================
    log_history(
        "이동",
        item_code,
        qty,
        f"{from_location} → {to_location}"
    )

    conn.commit()
    conn.close()

    # =========================
    # 5️⃣ 작업자 메인 이동
    # =========================
    return RedirectResponse(url="/worker", status_code=303)
