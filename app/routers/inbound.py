from fastapi import APIRouter, Form
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/inbound")

@router.post("")
def inbound(
    warehouse: str = Form(...),
    location: str = Form(...),
    item_code: str = Form(...),
    item_name: str = Form(""),
    lot_no: str = Form(""),
    spec: str = Form(""),
    qty: float = Form(...)
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO inventory
        (warehouse, location, item_code, item_name, lot_no, spec, qty)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET qty = qty + excluded.qty
    """, (warehouse, location, item_code, item_name, lot_no, spec, qty))

    log_history("IN", warehouse, location, item_code, lot_no, qty, "입고")

    conn.commit()
    conn.close()
    return {"result": "OK"}
