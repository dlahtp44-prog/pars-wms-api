from fastapi import APIRouter, Form
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/move")

@router.post("")
def move(
    warehouse: str = Form(...),
    from_location: str = Form(...),
    to_location: str = Form(...),
    item_code: str = Form(...),
    lot_no: str = Form(""),
    qty: float = Form(...)
):
    conn = get_conn()
    cur = conn.cursor()

    # 출고
    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, warehouse, from_location, item_code, lot_no))

    # 입고
    cur.execute("""
        INSERT INTO inventory
        (warehouse, location, item_code, lot_no, qty)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET qty = qty + excluded.qty
    """, (warehouse, to_location, item_code, lot_no, qty))

    log_history("MOVE", warehouse, from_location, item_code, lot_no, -qty, "이동 출고")
    log_history("MOVE", warehouse, to_location, item_code, lot_no, qty, "이동 입고")

    conn.commit()
    conn.close()
    return {"result": "OK"}
