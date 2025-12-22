from fastapi import APIRouter
from pydantic import BaseModel
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/qr")

class QR(BaseModel):
    qr: str

@router.post("/process")
def process(qr: QR):
    # tx|warehouse|from_loc|to_loc|item|lot|qty
    tx, w, f, t, i, lot, qty = qr.qr.split("|")
    qty = float(qty)

    conn = get_conn()
    cur = conn.cursor()

    if tx == "IN":
        cur.execute("""
        INSERT INTO inventory (warehouse, location, item_code, lot_no, qty)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET qty = qty + excluded.qty
        """, (w, t, i, lot, qty))

    elif tx == "OUT":
        cur.execute("""
        UPDATE inventory SET qty = qty - ?
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
        """, (qty, w, f, i, lot))

    elif tx == "MOVE":
        cur.execute("""
        UPDATE inventory SET qty = qty - ?
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
        """, (qty, w, f, i, lot))

        cur.execute("""
        INSERT INTO inventory (warehouse, location, item_code, lot_no, qty)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET qty = qty + excluded.qty
        """, (w, t, i, lot, qty))

    conn.commit()
    conn.close()
    log_history(tx, w, f, i, lot, qty)
    return {"result":"OK"}
