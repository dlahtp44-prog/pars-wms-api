# app/routers/upload_inventory.py

from fastapi import APIRouter, UploadFile, File
import csv, io
from app.db import get_conn, log_history

router = APIRouter(
    prefix="/api/inbound",
    tags=["입고 업로드"]
)


@router.post("/upload")
def upload_inventory(file: UploadFile = File(...)):
    """
    입고 CSV 업로드
    - 영문/한글 컬럼 자동 대응
    - 재고 UPSERT
    - 이력 기록
    """

    content = file.file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))

    conn = get_conn()
    cur = conn.cursor()

    for r in reader:
        # ===== 컬럼 자동 매핑 =====
        warehouse = r.get("warehouse") or r.get("창고", "")
        location = r.get("location") or r.get("로케이션", "")
        brand = r.get("brand") or r.get("브랜드", "")
        item_code = r.get("item_code") or r.get("품번", "")
        item_name = r.get("item_name") or r.get("품명", "")
        lot_no = (
            r.get("lot_no")
            or r.get("LOT")
            or r.get("LOT NO")
            or ""
        )
        spec = r.get("spec") or r.get("규격", "")
        qty = float(r.get("qty") or r.get("수량") or 0)

        # ===== 재고 UPSERT =====
        cur.execute("""
            INSERT INTO inventory
            (warehouse, location, brand, item_code, item_name, lot_no, spec, qty)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(warehouse, location, item_code, lot_no)
            DO UPDATE SET
                brand = excluded.brand,
                item_name = excluded.item_name,
                spec = excluded.spec,
                qty = qty + excluded.qty
        """, (
            warehouse,
            location,
            brand,
            item_code,
            item_name,
            lot_no,
            spec,
            qty
        ))

        # ===== 이력 기록 =====
        log_history(
            tx_type="IN",
            warehouse=warehouse,
            location=location,
            item_code=item_code,
            lot_no=lot_no,
            qty=qty,
            remark="CSV 입고 업로드"
        )

    conn.commit()
    conn.close()

    return {
        "result": "OK",
        "message": "입고 엑셀 업로드 완료"
    }
