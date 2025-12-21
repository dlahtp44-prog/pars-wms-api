from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from app.db import get_conn, log_history, log_qr_error

router = APIRouter(prefix="/api/qr", tags=["QR"])

@router.post("/process")
def qr_process(qr: str):
    try:
        # OUT|WH=서이천창고|FROM=D01-01|ITEM=728750|QTY=8
        # MOVE|WH=서이천창고|FROM=D01-01|TO=D02-03|ITEM=728750|QTY=5
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

        if action not in ("OUT", "MOVE"):
            raise ValueError("TYPE은 OUT 또는 MOVE만 허용")

        if action == "MOVE" and not to_loc:
            raise ValueError("MOVE에는 TO= 로케이션이 필요")

    except Exception as e:
        log_qr_error(qr_raw=qr, err_type="PARSE_ERROR", err_msg=str(e))
        raise HTTPException(400, f"QR 형식 오류: {e}")

    conn = get_conn()
    cur = conn.cursor()

    try:
        # FIFO LOT 조회
        cur.execute("""
            SELECT id, lot_no, qty
            FROM inventory
            WHERE warehouse=? AND location=? AND item_code=? AND qty > 0
            ORDER BY id ASC
        """, (warehouse, from_loc, item_code))

        lots = cur.fetchall()
        if not lots:
            log_qr_error(qr_raw=qr, err_type="NO_STOCK", err_msg="재고 없음")
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

            # 이동이면 도착지 추가
            if action == "MOVE":
                cur.execute("""
                    INSERT INTO inventory (warehouse, location, item_code, lot_no, qty)
                    VALUES (?, ?, ?, ?, ?)
                """, (warehouse, to_loc, item_code, lot["lot_no"], deduct))

            # 이력
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
            log_qr_error(qr_raw=qr, err_type="LACK_QTY", err_msg="수량 부족")
            raise HTTPException(400, "수량 부족")

        conn.commit()

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        log_qr_error(qr_raw=qr, err_type="SERVER_ERROR", err_msg=str(e))
        raise HTTPException(500, "서버 처리 오류")
    finally:
        conn.close()

    return RedirectResponse("/worker", status_code=303)
