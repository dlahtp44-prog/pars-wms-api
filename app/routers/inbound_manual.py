from fastapi import APIRouter
from pydantic import BaseModel
from app.db import add_inventory, log_history

router = APIRouter(prefix="/api/inbound/manual", tags=["수동입고"])

class ManualInbound(BaseModel):
    warehouse: str
    location: str
    item_code: str
    lot_no: str
    qty: float

@router.post("")
def inbound_manual(data: ManualInbound):
    if data.qty <= 0:
        return {"ok": False, "msg": "수량은 0보다 커야 합니다"}

    add_inventory(
        warehouse=data.warehouse,
        location=data.location,
        item_code=data.item_code,
        lot_no=data.lot_no,
        qty=data.qty
    )

    log_history(
        tx_type="IN",
        warehouse=data.warehouse,
        location=data.location,
        item_code=data.item_code,
        lot_no=data.lot_no,
        qty=data.qty,
        remark="수동 입고"
    )

    return {"ok": True}
