# app/routers/inbound_manual.py
from fastapi import APIRouter, Query
from app.db import get_conn, log_history

router = APIRouter(
    prefix="/api/inbound",
    tags=["Inbound"]
)

@router.get("/manual")
def inbound_manual(
    item_code: str = Query(...),
    item_name: str = Query(""),
    spec: str = Query(""),
    lot_no: str = Query(""),
    location: str = Query(""),
    warehouse: str = Query("DEFAULT"),
    qty: float = Query(...)
):
    conn = get_conn()
    cur = conn.cursor()

    # 재고 반영 (UPSERT)
    cur.execute("""
        INSERT INTO inventory
        (warehouse, location, item_code, item_name, lot_no, spec, qty)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET
            qty = qty + excluded.qty
    """, (
        warehouse,
        location,
        item_code,
        item_name,
        lot_no,
        spec,
        qty
    ))

    # 이력 기록
    log_history(
        tx_type="IN",
        warehouse=warehouse,
        location=location,
        item_code=item_code,
        lot_no=lot_no,
        qty=qty,
        remark="수동 입고"
    )

    conn.commit()
    conn.close()

    return {
        "result": "OK",
        "msg": "수동 입고 완료",
        "item_code": item_code,
        "lot_no": lot_no,
        "qty": qty
    }
