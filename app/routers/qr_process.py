from fastapi import APIRouter
from pydantic import BaseModel
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/qr")

class QR(BaseModel):
    qr: str

@router.post("/process")
def process(qr: QR):
    # 예: warehouse|location|item_code|lot|qty
    w, l, i, lot, qty = qr.qr.split("|")
    qty = float(qty)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO inventory (warehouse, location, item_code, lot_no, qty)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET qty = qty + excluded.qty
    """, (w, l, i, lot, qty))
    conn.commit()
    conn.close()

    log_history("QR", w, l, i, lot, qty)
    return {"ok": True}
