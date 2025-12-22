from fastapi import APIRouter, Form, HTTPException
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/outbound")

@router.post("")
def outbound(
    warehouse: str = Form(...),
    location: str = Form(...),
    item_code: str = Form(...),
    lot_no: str = Form(""),
    qty: float = Form(...)
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT qty FROM inventory
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, location, item_code, lot_no))

    row = cur.fetchone()
    if not row or row["qty"] < qty:
        raise HTTPException(400, "재고 부족")

    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, warehouse, location, item_code, lot_no))

    log_history("OUT", warehouse, location, item_code, lot_no, -qty, "출고")

    conn.commit()
    conn.close()
    return {"result": "OK"}
