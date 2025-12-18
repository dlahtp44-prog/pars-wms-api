from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
from app.db import get_conn, log_history

router = APIRouter(prefix="/api", tags=["입고"])

@router.post("/inbound")
def inbound(
    location_name: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(""),
    spec: str = Form(""),
    lot_no: str = Form(""),
    location: str = Form(...),
    qty: int = Form(...)
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO inventory
        (location_name, brand, item_code, item_name, lot_no, spec, location, qty)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(item_code, location)
        DO UPDATE SET qty = qty + ?
    """, (
        location_name, brand, item_code, item_name,
        lot_no, spec, location, qty, qty
    ))

    log_history("입고", item_code, qty, location)
    conn.commit()
    conn.close()

    return RedirectResponse("/worker", status_code=303)
