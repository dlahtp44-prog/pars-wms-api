from fastapi import APIRouter, Form, HTTPException
from app.db import get_conn, log_history

router = APIRouter(
    prefix="/api/outbound",
    tags=["Outbound"]
)

@router.post("")
def outbound(
    warehouse: str = Form(...),
    location: str = Form(...),
    item_code: str = Form(...),
    item_name: str = Form(""),
    brand: str = Form(""),
    lot_no: str = Form(""),
    spec: str = Form(""),
    qty: float = Form(...)
):
    conn = get_conn()
    cur = conn.cursor()

    # 1️⃣ 현재 재고 확인
    cur.execute("""
        SELECT qty
        FROM inventory
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, location, item_code, lot_no))

    row = cur.fetchone()
    current_qty = row["qty"] if row else 0

    if current_qty < qty:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail=f"재고 부족 (현재 {current_qty})"
        )

    # 2️⃣ 재고 차감 (UPSERT)
    cur.execute("""
        INSERT INTO inventory
        (warehouse, location, brand, item_code, item_name, lot_no, spec, qty)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET qty = qty - excluded.qty
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

    # 3️⃣ 이력 기록
    log_history(
        tx_type="출고",
        warehouse=warehouse,
        location=location,
        item_code=item_code,
        lot_no=lot_no,
        qty=-qty,
        remark="출고 처리"
    )

    conn.commit()
    conn.close()

    return {"result": "출고 완료"}
