from fastapi import APIRouter, HTTPException
from app.db import is_blocked_action

router = APIRouter(prefix="/api/move")

@router.post("")
def move():
    if is_blocked_action("MOVE"):
        raise HTTPException(
            status_code=403,
            detail="QR 오류 누적으로 이동이 차단됨"
        )
    return {"result": "이동 처리"}


@router.post("")
def move_inventory(
    warehouse: str = Form(...),

    from_location: str = Form(...),
    to_location: str = Form(...),

    item_code: str = Form(...),
    item_name: str = Form(""),
    brand: str = Form(""),
    lot_no: str = Form(""),
    spec: str = Form(""),

    qty: float = Form(...)
):
    conn = get_conn()
    cur = conn.cursor()

    try:
        # =========================
        # 1️⃣ 출발지 재고 확인
        # =========================
        cur.execute("""
            SELECT qty
            FROM inventory
            WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
        """, (warehouse, from_location, item_code, lot_no))

        row = cur.fetchone()
        current_qty = row["qty"] if row else 0

        if current_qty < qty:
            raise HTTPException(
                status_code=400,
                detail=f"이동 불가: 출발지 재고 부족 (현재 {current_qty})"
            )

        # =========================
        # 2️⃣ 출발지 재고 차감
        # =========================
        cur.execute("""
            INSERT INTO inventory
            (warehouse, location, brand, item_code, item_name, lot_no, spec, qty)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(warehouse, location, item_code, lot_no)
            DO UPDATE SET qty = qty - excluded.qty
        """, (
            warehouse,
            from_location,
            brand,
            item_code,
            item_name,
            lot_no,
            spec,
            qty
        ))

        # =========================
        # 3️⃣ 도착지 재고 증가
        # =========================
        cur.execute("""
            INSERT INTO inventory
            (warehouse, location, brand, item_code, item_name, lot_no, spec, qty)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(warehouse, location, item_code, lot_no)
            DO UPDATE SET qty = qty + excluded.qty
        """, (
            warehouse,
            to_location,
            brand,
            item_code,
            item_name,
            lot_no,
            spec,
            qty
        ))

        # =========================
        # 4️⃣ 이력 기록 (이동)
        # =========================
        log_history(
            tx_type="이동",
            warehouse=warehouse,
            location=f"{from_location} → {to_location}",
            item_code=item_code,
            lot_no=lot_no,
            qty=qty,
            remark="재고 이동"
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    return {"result": "재고 이동 완료"}
