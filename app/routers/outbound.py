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

    # 현재 재고 조회
    row = cur.execute("""
        SELECT * FROM inventory
        WHERE item_code=? AND lot_no=? AND location=?
    """, (item_code, lot_no, location)).fetchone()

    if not row or row["qty"] < qty:
        conn.close()
        raise HTTPException(400, "출고 재고 부족")

    # 재고 차감
    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?
        WHERE item_code=? AND lot_no=? AND location=?
    """, (qty, item_code, lot_no, location))

    # 이력 기록
    log_history("출고", {
        **row,
        "qty": qty
    })

    conn.commit()
    conn.close()

    return RedirectResponse("/inventory-page", status_code=303)
