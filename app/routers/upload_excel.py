from fastapi import APIRouter, UploadFile, File
import csv, io
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/excel")

@router.post("/upload")
def upload_excel(file: UploadFile = File(...)):
    content = file.file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))

    conn = get_conn()
    cur = conn.cursor()

    for r in reader:
        tx = r["tx_type"]   # IN / OUT
        qty = float(r["qty"])
        if tx == "OUT":
            qty = -qty

        cur.execute("""
            INSERT INTO inventory
            (warehouse, location, item_code, item_name, lot_no, shade, qty)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(warehouse, location, item_code, lot_no)
            DO UPDATE SET qty = qty + excluded.qty
        """, (
            r["warehouse"], r["location"],
            r["item_code"], r["item_name"],
            r["lot_no"], r.get("shade",""), qty
        ))

        log_history(tx, r["warehouse"], r["location"],
                    r["item_code"], r["lot_no"], qty)

    conn.commit()
    conn.close()
    return {"result": "엑셀 처리 완료"}
