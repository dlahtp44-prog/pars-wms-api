from fastapi import APIRouter, HTTPException
from app.db import is_blocked_action

router = APIRouter(prefix="/api/outbound")

@router.post("")
def outbound():
    if is_blocked_action("OUT"):
        raise HTTPException(
            status_code=403,
            detail="QR 오류 누적으로 출고가 차단됨"
        )
    return {"result": "출고 처리"}

    conn = get_conn()
    cur = conn.cursor()

    try:
        # =========================
        # 1️⃣ FIFO 대상 LOT 조회
        # =========================
        cur.execute("""
            SELECT id, lot_no, qty
            FROM inventory
            WHERE warehouse=? AND location=? AND item_code=? AND qty > 0
            ORDER BY id ASC
        """, (warehouse, location, item_code))

        rows = cur.fetchall()

        if not rows:
            raise HTTPException(400, "출고 가능한 재고 없음")

        remain = qty

        # =========================
        # 2️⃣ LOT 순서대로 차감
        # =========================
        for r in rows:
            if remain <= 0:
                break

            lot_qty = r["qty"]
            lot_no = r["lot_no"]

            deduct = min(lot_qty, remain)

            cur.execute("""
                UPDATE inventory
                SET qty = qty - ?
                WHERE id = ?
            """, (deduct, r["id"]))

            # =========================
            # 3️⃣ 출고 이력 기록 (LOT별)
            # =========================
            log_history(
                tx_type="출고",
                warehouse=warehouse,
                location=location,
                item_code=item_code,
                lot_no=lot_no,
                qty=deduct,
                remark="FIFO 출고"
            )

            remain -= deduct

        if remain > 0:
            raise HTTPException(
                400,
                f"출고 수량 부족 (요청 {qty}, 가능 {qty-remain})"
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    return {"result": "FIFO 출고 완료"}
