from fastapi import APIRouter, Form
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/inbound", tags=["입고"])

@router.post("")
def inbound(
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
        (location_name, item_code, item_name, lot_no, spec, location, qty)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(item_code, location)
        DO UPDATE SET qty = qty + ?
    """, (
        location_name, item_code, item_name,
        lot_no, spec, location, qty, qty
    ))

    log_history("입고", item_code, qty, location)

    conn.commit()
    conn.close()

    return {"result": "입고 완료"}
