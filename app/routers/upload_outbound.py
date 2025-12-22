from fastapi import APIRouter, UploadFile, File
import csv, io
from app.db import get_conn, log_history

router = APIRouter(prefix="/api", tags=["업로드"])

@router.post("/outbound/upload")
def upload_outbound(file: UploadFile = File(...)):
    content = file.file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))

    conn = get_conn()
    cur = conn.cursor()

    for r in reader:
        warehouse = r.get("warehouse", "") or r.get("창고", "")
        location = r.get("location", "") or r.get("로케이션", "")
        item_code = r.get("item_code", "") or r.get("품번", "")
        lot_no = r.get("lot_no", "") or r.get("LOT", "") or r.get("LOT NO", "")
        qty = float(r.get("qty", 0) or r.get("수량", 0) or 0)
        remark = r.get("remark", "") or r.get("비고", "")

        cur.execute("""
            INSERT INTO inventory (warehouse, location, item_code, lot_no, qty, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(warehouse, location, item_code, lot_no)
            DO UPDATE SET
                qty = qty - excluded.qty,
                updated_at=CURRENT_TIMESTAMP
        """, (warehouse, location, item_code, lot_no, qty))

        log_history("출고", warehouse, location, item_code, "", lot_no, "", qty, f"CSV 업로드 {remark}")

    conn.commit()
    conn.close()
    return {"result": "OK", "msg": "출고 업로드 완료"}
