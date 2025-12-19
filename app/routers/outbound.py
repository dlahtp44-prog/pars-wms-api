from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import RedirectResponse
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/outbound", tags=["출고"])

@router.post("")
def outbound(
    item_code: str = Form(...),
    location: str = Form(...),
    qty: int = Form(...)
):
    conn = get_conn()
    cur = conn.cursor()

    row = cur.execute(
        "SELECT qty FROM inventory WHERE item_code=? AND location=?",
        (item_code, location)
    ).fetchone()

    if not row or row["qty"] < qty:
        conn.close()
        raise HTTPException(400, "재고 부족")

    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?
        WHERE item_code=? AND location=?
    """, (qty, item_code, location))

    log_history("출고", item_code, qty, location)

    conn.commit()
    conn.close()

    return RedirectResponse("/worker/inventory", status_code=303)
