# app/routers/inbound.py
from fastapi import APIRouter, Form, HTTPException
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/inbound", tags=["Inbound"])


@router.post("")
def inbound(
    warehouse: str = Form(...),
    location: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(...),
    lot_no: str = Form(""),
    spec: str = Form(""),
    qty: float = Form(...)
):
    if qty <= 0:
        raise HTTPException(status_code=400, detail="입고 수량은 0보다 커야 합니다")

    conn = get_conn()
    cur = conn.cursor()

    # 1️⃣ 재고 반영 (UPSERT)
    cur.execute("""
        INSERT INTO inventory
        (warehouse, location, brand, item_code, item_name, lot_no, spec, qty)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET qty = qty + excluded.qty
    """, (
        warehouse,
        location,
        brand,
        item_code,
        item_name,
        lot_no,
        spec,
        qty
    ))

    conn.commit()
    conn.close()

    # 2️⃣ 이력 자동 기록
    log_history(
        tx_type="IN",
        warehouse=warehouse,
        location=location,
        item_code=item_code,
        lot_no=lot_no,
        qty=qty,
        remark="입고 처리"
    )

    return {
        "result": "OK",
        "message": "입고 처리 완료"
    }
