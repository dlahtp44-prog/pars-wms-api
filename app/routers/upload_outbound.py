from fastapi import APIRouter, UploadFile, File, HTTPException
import csv, io
from app.db import get_conn, log_history

router = APIRouter(
    prefix="/api/outbound",
    tags=["Outbound"]
)

@router.post("/upload")
def upload_outbound_fifo(file: UploadFile = File(...)):
    content = file.file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))

    conn = get_conn()
    cur = conn.cursor()

    try:
        for r in reader:
            warehouse = r["warehouse"]
            location = r["location"]
            item_code = r["item_code"]
            qty = float(r["qty"])

            # =========================
            # FIFO 대상 LOT 조회
            # =========================
            cur.execute("""
                SELECT id, lot_no, qty
                FROM inventory
                WHERE warehouse=? AND location=? AND item_code=? AND qty > 0
                ORDER BY id ASC
            """, (warehouse, location, item_code))

            lots = cur.fetchall()
            if not lots:
                raise HTTPException(
                    400,
                    f"출고 불가: {item_code} 재고 없음"
                )

            remain = qty

            # =========================
            # FIFO 차감
            # =========================
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
                    remark="엑셀 FIFO 출고"
                )

                remain -= deduct

            if remain > 0:
                raise HTTPException(
                    400,
                    f"{item_code} 출고 수량 부족"
                )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    return {"result": "엑셀 FIFO 출고 완료"}
