from fastapi import APIRouter
from pydantic import BaseModel
from app.db import move_inventory

router = APIRouter(prefix="/api/qr")

class QRMove(BaseModel):
    from_location: str
    to_location: str
    item_code: str
    lot_no: str
    qty: float
    warehouse: str = "MAIN"

@router.post("/process")
def process_qr(data: QRMove):
    move_inventory(
        warehouse=data.warehouse,
        from_location=data.from_location,
        to_location=data.to_location,
        item_code=data.item_code,
        lot_no=data.lot_no,
        qty=data.qty
    )
    return {"ok": True}
