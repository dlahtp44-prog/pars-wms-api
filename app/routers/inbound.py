from fastapi import APIRouter, Form
from app.db import get_conn, log_history

router = APIRouter(prefix="/api", tags=["입고"])

@router.post("/inbound")
def inbound(
    warehouse: str = Form(...),
    location: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(""),
    lot_no: str = Form(...),
    spec: str = Form(""),
    qty: float = Form(...)
):
    conn = get_conn()
    cur = conn.cursor()

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

    conn.commit()
    conn.close()

    log_history("입고", warehouse, location, item_code, item_name, lot_no, spec, qty, "")

    return {"result": "OK"}
