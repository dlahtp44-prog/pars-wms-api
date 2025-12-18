from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import RedirectResponse
import csv, io
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/inbound", tags=["입고"])

# =========================
# 1️⃣ 수기 입고
# =========================
@router.post("")
def inbound(
    item_code: str = Form(...),
    item_name: str = Form(...),
    brand: str = Form(""),
    lot_no: str = Form(""),
    spec: str = Form(""),
    location: str = Form(...),
    qty: int = Form(...)
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO inventory (
            location_name, brand, item_code, item_name,
            lot_no, spec, location, qty
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(item_code, location)
        DO UPDATE SET qty = qty + excluded.qty
    """, (
        "", brand, item_code, item_name,
        lot_no, spec, location, qty
    ))

    log_history("입고", item_code, qty, location)

    conn.commit()
    conn.close()

    return RedirectResponse("/worker", status_code=303)

# =========================
# 2️⃣ 엑셀 업로드 입고
# =========================
@router.post("/upload")
def upload_inventory(file: UploadFile = File(...)):
    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))

    conn = get_conn()
    cur = conn.cursor()

    for r in reader:
        cur.execute("""
            INSERT INTO inventory (
                location_name, brand, item_code, item_name,
                lot_no, spec, location, qty
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(item_code, location)
            DO UPDATE SET qty = qty + excluded.qty
        """, (
            r.get("location_name", ""),
            r.get("brand", ""),
            r["item_code"],
            r["item_name"],
            r.get("lot_no", ""),
            r.get("spec", ""),
            r["location"],
            int(r["qty"])
        ))

        log_history("입고", r["item_code"], int(r["qty"]), r["location"])

    conn.commit()
    conn.close()

    return RedirectResponse("/inventory-page", status_code=303)
