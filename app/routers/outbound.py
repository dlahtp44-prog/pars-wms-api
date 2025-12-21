from fastapi import APIRouter, Form, HTTPException
from app.db import get_conn, log_history

router = APIRouter(prefix="/api", tags=["출고"])

@router.post("/outbound")
def outbound(
    warehouse: str = Form(...),
    location: str = Form(...),
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
    """, (warehouse, location, item_code, lot_no)).fetchone()

    current_qty = float(row["qty"] or 0)
    if current_qty < qty:
        conn.close()
        raise HTTPException(400, f"재고 부족 (현재 {current_qty})")

    # 출고는 -qty 기록으로 남김
    cur.execute("""
        INSERT INTO inventory (warehouse, location, item_code, lot_no, qty, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET
            qty = qty - excluded.qty,
            updated_at=CURRENT_TIMESTAMP
    """, (warehouse, location, item_code, lot_no, qty))

    conn.commit()
    conn.close()

    log_history("출고", warehouse, location, item_code, "", lot_no, "", qty, remark)

    return {"result": "OK"}
