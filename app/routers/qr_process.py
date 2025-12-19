from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from app.db import get_conn, log_history

router = APIRouter(
    prefix="/api/qr",
    tags=["QR"]
)

@router.post("/process")
def qr_process(qr: str):
    """
    QR 예시
    OUT|WH=서이천창고|FROM=D01-01|ITEM=728750|QTY=8
    MOVE|WH=서이천창고|FROM=D01-01|TO=D02-03|ITEM=728750|QTY=5
    """

    # -------------------------
    # QR 파싱
    # -------------------------
    try:
        parts = dict(
            p.split("=") if "=" in p else ("TYPE", p)
            for p in qr.split("|")
        )

        action = parts["TYPE"]
        warehouse = parts["WH"]
        from_loc = parts["FROM"]
        item_code = parts["ITEM"]
        qty = float(parts["QTY"])
        to_loc = parts.get("TO")

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
    """, (warehouse, from_loc, item_code))

    lots = cur.fetchall()
    if not lots:
        conn.close()
        raise HTTPException(400, "재고 없음")

    remain = qty

    for lot in lots:
        if remain <= 0:
            break

        deduct = min(lot["qty"], remain)

        # 출발지 차감
        cur.execute("""
            UPDATE inventory
            SET qty = qty - ?
            WHERE id = ?
        """, (deduct, lot["id"]))

        # =========================
        # 이동일 경우 도착지 추가
        # =========================
        if action == "MOVE":
            cur.execute("""
                INSERT INTO inventory
                (warehouse, location, item_code, lot_no, qty)
                VALUES (?, ?, ?, ?, ?)
            """, (
                warehouse,
                to_loc,
                item_code,
                lot["lot_no"],
                deduct
            ))

        # =========================
        # 작업이력
        # =========================
        log_history(
            tx_type="출고" if action == "OUT" else "이동",
            warehouse=warehouse,
            location=from_loc if action == "OUT" else f"{from_loc} → {to_loc}",
            item_code=item_code,
            lot_no=lot["lot_no"],
            qty=deduct,
            remark="QR FIFO 자동"
        )

        remain -= deduct

    if remain > 0:
        conn.rollback()
        conn.close()
        raise HTTPException(400, "수량 부족")

    conn.commit()
    conn.close()

    # ✅ 처리 후 작업자 메인 복귀
    return RedirectResponse("/worker", status_code=303)
