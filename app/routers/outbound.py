from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import RedirectResponse
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/outbound", tags=["출고"])

@router.post("")
def outbound(
    item_code: str = Form(...),
    item_name: str = Form(...),
    spec: str = Form(...),
    lot_no: str = Form(...),
    location_name: str = Form(...),
    location: str = Form(...),
    qty: int = Form(...)
):
    conn = get_conn()
    cur = conn.cursor()

    # =========================
    # 1️⃣ 재고 확인
    # =========================
    row = cur.execute("""
        SELECT qty
        FROM inventory
        WHERE item_code = ?
          AND lot_no = ?
          AND location = ?
    """, (item_code, lot_no, location)).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=400, detail="재고 없음")

    if row["qty"] < qty:
        conn.close()
        raise HTTPException(status_code=400, detail="출고 수량 초과")

    # =========================
    # 2️⃣ 재고 차감
    # =========================
    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?
        WHERE item_code = ?
          AND lot_no = ?
          AND location = ?
    """, (qty, item_code, lot_no, location))

    # =========================
    # 3️⃣ 작업 이력 기록
    # =========================
    log_history(
        "출고",
        item_code,
        qty,
        location
    )

    conn.commit()
    conn.close()

    # =========================
    # 4️⃣ 작업자 메인 이동
    # =========================
    return RedirectResponse(url="/worker", status_code=303)
