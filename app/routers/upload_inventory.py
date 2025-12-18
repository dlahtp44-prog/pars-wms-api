from fastapi import APIRouter, UploadFile, File
import sqlite3, csv, io
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/upload", tags=["엑셀업로드"])

@router.post("/inventory")
async def upload_inventory(file: UploadFile = File(...)):
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))

    conn = get_conn()
    cur = conn.cursor()

    for row in reader:
        cur.execute("""
            INSERT INTO inventory
            (location_name, brand, item_code, item_name, lot_no, spec, location, qty)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(item_code, location)
            DO UPDATE SET qty = qty + excluded.qty
        """, (
            row["장소명"],
            row["브랜드"],
            row["품번"],
            row["품명"],
            row["LOT"],
            row["규격"],
            row["로케이션"],
            int(row["수량"])
        ))

        log_history("엑셀입고", row["품번"], row["수량"], row["로케이션"])

    conn.commit()
    conn.close()

    return {"result": "엑셀 업로드 완료"}

