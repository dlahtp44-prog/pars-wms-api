from fastapi import APIRouter, Query
from app.db import get_conn, log_history

router = APIRouter(
    prefix="/api/inbound-manual",
    tags=["Inbound Manual"]
)

@router.get("")
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

    cur.execute("""
        INSERT INTO inventory
        (warehouse, location, item_code, item_name, lot_no, spec, qty)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET qty = qty + excluded.qty
    """, (
        warehouse,
        location,
        item_code,
        item_name,
        lot_no,
        spec,
        qty
    ))

    log_history(
        tx_type="IN",
        warehouse=warehouse,
        location=location,
        item_code=item_code,
        lot_no=lot_no,
        qty=qty,
        remark="QR/수동 GET 입고"
    )

    conn.commit()
    conn.close()

    return {
        "ok": True,
        "msg": "입고 완료",
        "item_code": item_code,
        "lot_no": lot_no,
        "qty": qty
    }
