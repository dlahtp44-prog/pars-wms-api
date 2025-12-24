from fastapi import APIRouter
from pydantic import BaseModel
from app.db import add_inventory, subtract_inventory, move_inventory

router = APIRouter(prefix="/api/qr", tags=["qr"])

class QRBody(BaseModel):
    action: str  # IN / OUT / MOVE / LOCATION
    warehouse: str = "MAIN"

    # 공통
    location: str = ""
    item_code: str = ""
    item_name: str = ""
    lot_no: str = ""
    spec: str = ""
    brand: str = ""
    qty: float = 0

    # move
    from_location: str = ""
    to_location: str = ""

@router.post("/process")
def process_qr(b: QRBody):
    act = (b.action or "").upper().strip()

    if act == "IN":
        add_inventory(b.warehouse, b.location, b.brand, b.item_code, b.item_name, b.lot_no, b.spec, b.qty, remark="QR IN")
        return {"ok": True, "action": "IN"}

    if act == "OUT":
        subtract_inventory(b.warehouse, b.location, b.item_code, b.lot_no, b.qty, remark="QR OUT")
        return {"ok": True, "action": "OUT"}

    if act == "MOVE":
        move_inventory(b.warehouse, b.from_location, b.to_location, b.item_code, b.lot_no, b.qty, remark="QR MOVE")
        return {"ok": True, "action": "MOVE"}

    return {"ok": False, "detail": "지원하지 않는 action"}
