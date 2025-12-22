from fastapi import APIRouter
from pydantic import BaseModel
from app.db import get_conn, log_history

router = APIRouter(
    prefix="/api/inbound",
    tags=["Inbound"]
)

# =========================
# 요청 스키마
# =========================
class InboundManual(BaseModel):
    warehouse: str
    location: str
    brand: str | None = ""
    item_code: str
    item_name: str | None = ""
    lot_no: str
    spec: str | None = ""
    qty: float


# =========================
# 수동 입고 API
# =========================
@router.post("/manual")
def inbound_manual(data: InboundManual):
    conn = get_conn()
    cur = conn.cursor()

    # 재고 UPSERT
    cur.execute("""
        INSERT INTO inventory
        (warehouse, location, brand, item_code, item_name, lot_no, spec, qty)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET
            qty = qty + excluded.qty
    """, (
        data.warehouse,
        data.location,
        data.brand,
        data.item_code,
        data.item_name,
        data.lot_no,
        data.spec,
        data.qty
    ))

    # 이력 기록
    log_history(
        tx_type="IN",
        warehouse=data.warehouse,
        location=data.location,
        item_code=data.item_code,
        lot_no=data.lot_no,
        qty=data.qty,
        remark="수동 입고"
    )

    conn.commit()
    conn.close()

    return {
        "ok": True,
        "message": "수동 입고 완료"
    }
