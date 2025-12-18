from fastapi import APIRouter, UploadFile, File, HTTPException
import csv, io, json
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/upload", tags=["업로드"])

REQUIRED_COLUMNS = [
    "장소명", "브랜드", "품번", "품명",
    "LOT", "규격", "로케이션", "수량"
]

@router.post("/inventory-csv")
async def upload_inventory_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="CSV 파일만 가능")

    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))

    for col in REQUIRED_COLUMNS:
        if col not in reader.fieldnames:
            raise HTTPException(status_code=400, detail=f"필수 컬럼 누락: {col}")

    conn = get_conn()
    cur = conn.cursor()

    count = 0
    for row in reader:
        qty = int(row["수량"])

        qr_data = json.dumps({
            "type": "IN",
            "item": row["품번"],
            "lot": row["LOT"],
            "location": row["로케이션"],
            "qty": qty
        }, ensure_ascii=False)

        cur.execute("""
            INSERT INTO inventory
            (location_name, brand, item_code, item_name,
             lot_no, spec, location, qty, qr_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            qty,
            qr_data
        ))

        log_history("CSV입고", row["품번"], qty, row["로케이션"])
        count += 1

    conn.commit()
    conn.close()

    return {"result": "CSV 업로드 완료", "rows": count}
