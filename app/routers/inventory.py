from fastapi import APIRouter, UploadFile, File
import csv, io
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/inbound", tags=["입고"])

@router.post("/upload")
def upload_inventory(file: UploadFile = File(...)):
    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))

    conn = get_conn()
    cur = conn.cursor()

    for r in reader:
        cur.execute("""
            INSERT INTO inventory
            (location_name, brand, item_code, item_name, lot_no, spec, location, qty)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(item_code, location)
            DO UPDATE SET qty = qty + ?
        """, (
            r["location_name"], r["brand"], r["item_code"], r["item_name"],
            r["lot_no"], r["spec"], r["location"], int(r["qty"]), int(r["qty"])
        ))

        log_history("입고", r["item_code"], int(r["qty"]), r["location"])

    conn.commit()
    conn.close()

    return {"result": "엑셀 입고 완료"}
