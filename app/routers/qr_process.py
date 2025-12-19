from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from app.db import get_conn, log_history

router = APIRouter(
    prefix="/api/qr",
    tags=["QR"]
)

@router.post("/out")
def qr_fifo_out(qr: str):
    """
    QR 예시:
    OUT|WH=서이천창고|LOC=D01-01|ITEM=728750|QTY=8
    """

    try:
        parts = dict(
            p.split("=") if "=" in p else ("TYPE", p)
            for p in qr.split("|")
        )

        if parts["TYPE"] != "OUT":
            raise HTTPException(400, "출고 QR 아님")

        warehouse = parts["WH"]
        location = parts["LOC"]
        item_code = parts["ITEM"]
        qty = float(parts["QTY"])

    except Exception:
        raise HTTPException(400, "QR 형식 오류")

    conn = get_conn()
    cur = conn.cursor()

    # =========================
    # FIFO LOT 조회
    # =========================
    cur.execute("""
        SELECT id, lot_no, qty
        FROM inventory
        WHERE warehouse=? AND location=? AND item_code=? AND qty > 0
        ORDER BY id ASC
    """, (warehouse, location, item_code))

    lots = cur.fetchall()
    if not lots:
        conn.close()
        raise HTTPException(400, "출고 재고 없음")

    remain = qty

    for lot in lots:
        if remain <= 0:
            break

        deduct = min(lot["qty"], remain)

        cur.execute("""
            UPDATE inventory
            SET qty = qty - ?
            WHERE id = ?
        """, (deduct, lot["id"]))

        log_history(
            tx_type="출고",
            warehouse=warehouse,
            location=location,
            item_code=item_code,
            lot_no=lot["lot_no"],
            qty=deduct,
            remark="QR FIFO 출고"
        )

        remain -= deduct

    if remain > 0:
        conn.rollback()
        conn.close()
        raise HTTPException(400, "출고 수량 부족")

    conn.commit()
    conn.close()

    # ✅ 출고 후 작업자 메인으로 이동
    return RedirectResponse("/worker", status_code=303)
