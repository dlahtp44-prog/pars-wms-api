from fastapi import APIRouter, UploadFile, File, HTTPException
import csv, io
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/outbound", tags=["출고"])

@router.post("/upload")
def upload_outbound(file: UploadFile = File(...)):
    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))

    conn = get_conn()
    cur = conn.cursor()

    for r in reader:
        item_code = r["item_code"]
        location = r["location"]
        qty = int(r["qty"])

        row = cur.execute("""
            SELECT qty FROM inventory
            WHERE item_code=? AND location=?
        """, (item_code, location)).fetchone()

        if not row or row["qty"] < qty:
            conn.close()
            raise HTTPException(
                status_code=400,
                detail=f"{item_code} 재고 부족"
            )

        cur.execute("""
            UPDATE inventory
            SET qty = qty - ?
            WHERE item_code=? AND location=?
        """, (qty, item_code, location))

        log_history("출고", item_code, qty, location)

    conn.commit()
    conn.close()

    return {"result": "엑셀 출고 완료"}
