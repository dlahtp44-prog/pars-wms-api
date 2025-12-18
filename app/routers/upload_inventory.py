from fastapi import APIRouter, UploadFile, File, HTTPException
from app.db import get_conn, log_history
import csv
import io

router = APIRouter(prefix="/api", tags=["엑셀업로드"])

@router.post("/upload")
async def upload_inventory(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "CSV 파일만 허용")

    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))

    conn = get_conn()
    cur = conn.cursor()

    """
    CSV 컬럼 예시:
    type,location_name,brand,item_code,item_name,lot_no,spec,location,qty
    IN,서이천창고,FLORIM,728750,Walks/1.0,H5415,600x600,D01-01,10
    """

    for row in reader:
        tx_type = row["type"]
        item_code = row["item_code"]
        qty = int(row["qty"])
        location = row["location"]

        # 재고 처리
        if tx_type == "IN":
            cur.execute("""
                INSERT INTO inventory
                (location_name, brand, item_code, item_name, lot_no, spec, location, qty)
                VALUES (?,?,?,?,?,?,?,?)
                ON CONFLICT(item_code, location)
                DO UPDATE SET qty = qty + ?
            """, (
                row["location_name"], row["brand"], item_code,
                row["item_name"], row["lot_no"], row["spec"],
                location, qty, qty
            ))

        elif tx_type == "OUT":
            cur.execute("""
                UPDATE inventory
                SET qty = qty - ?
                WHERE item_code = ? AND location = ?
            """, (qty, item_code, location))

        elif tx_type == "MOVE":
            # 출발지 차감
            cur.execute("""
                UPDATE inventory
                SET qty = qty - ?
                WHERE item_code = ? AND location = ?
            """, (qty, item_code, row["from_location"]))

            # 도착지 증가
            cur.execute("""
                INSERT INTO inventory (item_code, location, qty)
                VALUES (?,?,?)
                ON CONFLICT(item_code, location)
                DO UPDATE SET qty = qty + ?
            """, (item_code, location, qty, qty))

        # 작업이력 기록
        log_history(tx_type, item_code, qty, location)

    conn.commit()
    conn.close()

    return {"result": "엑셀 업로드 완료"}
