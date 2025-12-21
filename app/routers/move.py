from fastapi import APIRouter, Form, HTTPException
from app.db import get_conn, log_history

router = APIRouter(prefix="/api", tags=["이동"])

@router.post("/move")
def move(
    warehouse: str = Form(...),
    from_location: str = Form(...),
    to_location: str = Form(...),
    item_code: str = Form(...),
    lot_no: str = Form(...),
    qty: float = Form(...),
    remark: str = Form("")
):
    conn = get_conn()
    cur = conn.cursor()

    row = cur.execute("""
        SELECT SUM(qty) as qty
        FROM inventory
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, from_location, item_code, lot_no)).fetchone()

    current_qty = float(row["qty"] or 0)
    if current_qty < qty:
        conn.close()
        raise HTTPException(400, f"재고 부족 (현재 {current_qty})")

    # 출발지 -
    cur.execute("""
        INSERT INTO inventory (warehouse, location, item_code, lot_no, qty, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET qty = qty - excluded.qty, updated_at=CURRENT_TIMESTAMP
    """, (warehouse, from_location, item_code, lot_no, qty))

    # 도착지 +
    cur.execute("""
        INSERT INTO inventory (warehouse, location, item_code, lot_no, qty, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET qty = qty + excluded.qty, updated_at=CURRENT_TIMESTAMP
    """, (warehouse, to_location, item_code, lot_no, qty))

    conn.commit()
    conn.close()

    log_history("이동", warehouse, from_location, item_code, "", lot_no, "", qty, f"→ {to_location} {remark}")

    return {"result": "OK"}
