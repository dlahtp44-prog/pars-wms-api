from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
from app.db import get_conn, log_history

router = APIRouter(prefix="/api", tags=["입고"])

@router.post("/inbound")
def inbound(
    item_code: str = Form(...),
    item_name: str = Form(...),
    brand: str = Form(...),
    lot_no: str = Form(...),
    spec: str = Form(...),
    location: str = Form(...),
    qty: int = Form(...)
):
    conn = get_conn()
    cur = conn.cursor()

    # 재고 반영
    cur.execute("""
        INSERT INTO inventory
        (item_code, item_name, brand, lot_no, spec, location, qty)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(item_code, lot_no, location)
        DO UPDATE SET qty = qty + excluded.qty
    """, (item_code, item_name, brand, lot_no, spec, location, qty))

    # 이력 기록 (같은 커서!)
    log_history(cur, "입고", item_code, lot_no, qty, location)

    conn.commit()
    conn.close()

    return RedirectResponse("/worker", status_code=303)
