from fastapi import APIRouter, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from app.db import get_conn, log_history
import csv
import io

router = APIRouter(prefix="/api/inbound", tags=["입고"])

# =========================
# 수기 입고
# =========================
@router.post("/manual")
def inbound_manual(
    item_code: str = Form(...),
    item_name: str = Form(...),
    spec: str = Form(...),
    lot_no: str = Form(...),
    location_name: str = Form(...),
    location: str = Form(...),
    qty: int = Form(...)
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO inventory
        (item_code, item_name, spec, lot_no, location_name, location, qty)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(item_code, lot_no, location)
        DO UPDATE SET qty = qty + ?
    """, (
        item_code, item_name, spec, lot_no,
        location_name, location, qty, qty
    ))

    log_history("입고", item_code, qty, location)
    conn.commit()
    conn.close()

    return RedirectResponse("/inventory-page", status_code=303)


# =========================
# CSV 업로드 입고
# =========================
@router.post("/upload")
def inbound_upload(file: UploadFile = File(...)):
    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))

    conn = get_conn()
    cur = conn.cursor()

    for row in reader:
        qty = int(row["qty"])
        cur.execute("""
            INSERT INTO inventory
            (item_code, item_name, spec, lot_no, location_name, location, qty)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(item_code, lot_no, location)
            DO UPDATE SET qty = qty + ?
        """, (
            row["item_code"],
            row["item_name"],
            row["spec"],
            row["lot_no"],
            row["location_name"],
            row["location"],
            qty,
            qty
        ))

        log_history("입고", row["item_code"], qty, row["location"])

    conn.commit()
    conn.close()

    return RedirectResponse("/inventory-page", status_code=303)
