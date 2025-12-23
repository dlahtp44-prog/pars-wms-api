from fastapi import APIRouter
from app.db import add_inventory

router = APIRouter(prefix="/api/inbound", tags=["입고"])
    prefix="/api/inbound",
    tags=["Inbound Manual"]
)

@router.get("/manual")
def inbound_manual(
    item_code: str = Query(...),
    item_name: str = Query(""),
    spec: str = Query(""),
    lot_no: str = Query(""),
    location: str = Query(...),
    location_name: str = Query(""),
    qty: float = Query(...),
    warehouse: str = Query("MAIN")
):
    """
    수동/QR 입고 처리 (querystring 방식)
    """

    conn = get_conn()
    cur = conn.cursor()
@router.post("/manual")
def inbound_manual(
    warehouse: str,
    location: str,
    brand: str = "",
    item_code: str = "",
    item_name: str = "",
    lot_no: str = "",
    spec: str = "",
    qty: float = 0
):
    add_inventory(
        warehouse, location, brand,
        item_code, item_name, lot_no, spec, qty
    )
    return {"result": "OK", "msg": "입고 완료"}
    # 1️⃣ inventory UPSERT (재고 증가)
    cur.execute("""
        INSERT INTO inventory
        (warehouse, location, brand, item_code, item_name, lot_no, spec, qty)
        VALUES (?, ?, '', ?, ?, ?, ?, ?)
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

    # 2️⃣ 이력 기록
    log_history(
        tx_type="IN",
        warehouse=warehouse,
        location=location,
        item_code=item_code,
        lot_no=lot_no,
        qty=qty,
        remark="수동/QR 입고"
    )

    conn.commit()
    conn.close()

    return {
        "result": "OK",
        "msg": "입고 처리 완료",
        "item_code": item_code,
        "lot_no": lot_no,
        "qty": qty
    }
