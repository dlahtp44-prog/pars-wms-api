from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import RedirectResponse
from app.db import get_conn, log_history

router = APIRouter(prefix="/api", tags=["출고"])

@router.post("/outbound")
def outbound(
    item_code: str = Form(...),
    lot_no: str = Form(...),
    location: str = Form(...),
    qty: int = Form(...)
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT qty FROM inventory
        WHERE item_code=? AND lot_no=? AND location=?
    """, (item_code, lot_no, location))

    row = cur.fetchone()
    if not row or row["qty"] < qty:
        conn.close()
        raise HTTPException(400, "재고 부족")

    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?
        WHERE item_code=? AND lot_no=? AND location=?
    """, (qty, item_code, lot_no, location))

    log_history(cur, "출고", item_code, lot_no, qty, location)

    conn.commit()
    conn.close()

    return RedirectResponse("/worker", status_code=303)
