from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import RedirectResponse
from app.db import get_conn, log_history

router = APIRouter(prefix="/api", tags=["출고"])

@router.post("/outbound")
def outbound(
    item_code: str = Form(...),
    qty: int = Form(...),
    location: str = Form(...)
):
    conn = get_conn()
    cur = conn.cursor()

    # 현재 재고 확인
    cur.execute(
        "SELECT qty FROM inventory WHERE item_code=? AND location=?",
        (item_code, location)
    )
    row = cur.fetchone()

    if not row or row["qty"] < qty:
        conn.close()
        raise HTTPException(status_code=400, detail="출고 재고 부족")

    # 재고 차감
    cur.execute(
        "UPDATE inventory SET qty = qty - ? WHERE item_code=? AND location=?",
        (qty, item_code, location)
    )

    log_history("출고", item_code, qty, location)

    conn.commit()
    conn.close()

    return RedirectResponse("/worker/outbound", status_code=303)
