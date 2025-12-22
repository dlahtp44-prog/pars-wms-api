from fastapi import APIRouter, UploadFile, File
import csv, io
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/inbound")

@router.post("/upload")
def upload_inventory(file: UploadFile = File(...)):
    content = file.file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))

    conn = get_conn()
    cur = conn.cursor()

    for r in reader:
        qty = float(r["수량"])
        cur.execute("""
            INSERT INTO inventory
            (warehouse, location, item_code, item_name, lot_no, spec, qty)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(warehouse, location, item_code, lot_no)
            DO UPDATE SET qty = qty + excluded.qty
        """, (
            r["창고"], r["로케이션"], r["품번"],
            r["품명"], r["LOT"], r["규격"], qty
        ))

        log_history("IN", r["창고"], r["로케이션"],
                    r["품번"], r["LOT"], qty, "엑셀 입고")

    conn.commit()
    conn.close()
    return {"result": "OK"}
