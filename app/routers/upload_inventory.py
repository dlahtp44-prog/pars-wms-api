from fastapi import APIRouter, UploadFile, File
import csv, io
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/inbound")

@router.post("/upload")
def upload_inventory(file: UploadFile = File(...)):
    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))

    conn = get_conn()
    cur = conn.cursor()

    for r in reader:
        cur.execute("""
            INSERT INTO inventory
            (warehouse, location, brand, item_code, item_name, lot_no, spec, qty)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(warehouse, location, item_code, lot_no)
            DO UPDATE SET qty = qty + ?
        """, (
            r["warehouse"], r["location"], r["brand"],
            r["item_code"], r["item_name"], r["lot_no"],
            r["spec"], int(r["qty"]), int(r["qty"])
        ))

        log_history("IN", r["warehouse"], r["location"],
                    r["item_code"], r["lot_no"], int(r["qty"]))

    conn.commit()
    conn.close()
    return {"result": "입고 엑셀 처리 완료"}

router = APIRouter(prefix="/api", tags=["업로드"])

@router.post("/inbound/upload")
def upload_inbound(file: UploadFile = File(...)):
    content = file.file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))

    conn = get_conn()
    cur = conn.cursor()

    for r in reader:
        warehouse = r.get("warehouse", "") or r.get("창고", "")
        location = r.get("location", "") or r.get("로케이션", "")
        brand = r.get("brand", "") or r.get("브랜드", "")
        item_code = r.get("item_code", "") or r.get("품번", "")
        item_name = r.get("item_name", "") or r.get("품명", "")
        lot_no = r.get("lot_no", "") or r.get("LOT", "") or r.get("LOT NO", "")
        spec = r.get("spec", "") or r.get("규격", "")
        qty = float(r.get("qty", 0) or r.get("수량", 0) or 0)

        cur.execute("""
            INSERT INTO inventory (warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(warehouse, location, item_code, lot_no)
            DO UPDATE SET
                brand=excluded.brand,
                item_name=excluded.item_name,
                spec=excluded.spec,
                qty = qty + excluded.qty,
                updated_at=CURRENT_TIMESTAMP
        """, (warehouse, location, brand, item_code, item_name, lot_no, spec, qty))

        log_history("입고", warehouse, location, item_code, item_name, lot_no, spec, qty, "CSV 업로드")

    conn.commit()
    conn.close()
    return {"result": "OK", "msg": "입고 업로드 완료"}
