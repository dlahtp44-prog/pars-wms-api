from fastapi import APIRouter
from pydantic import BaseModel
from app.db import add_inventory, move_inventory, log_history

router = APIRouter(prefix="/api/qr", tags=["QR 처리"])

class QRPayload(BaseModel):
    # type: IN / OUT / MOVE
    type: str
    warehouse: str = ""
    location: str = ""
    from_location: str = ""
    to_location: str = ""
    brand: str = ""
    item_code: str
    item_name: str = ""
    lot_no: str = ""
    spec: str = ""
    qty: float = 0

@router.post("/process")
def process_qr(p: QRPayload):
    t = (p.type or "").upper()
    qty = float(p.qty or 0)

    if t == "IN":
        add_inventory(p.warehouse, p.location, p.brand, p.item_code, p.item_name, p.lot_no, p.spec, abs(qty))
        log_history("IN", p.warehouse, p.location, p.item_code, p.item_name, p.brand, p.lot_no, p.spec, abs(qty), "QR")
        return {"ok": True, "msg": "입고 처리 완료"}

    if t == "OUT":
        add_inventory(p.warehouse, p.location, p.brand, p.item_code, p.item_name, p.lot_no, p.spec, -abs(qty))
        log_history("OUT", p.warehouse, p.location, p.item_code, p.item_name, p.brand, p.lot_no, p.spec, abs(qty), "QR")
        return {"ok": True, "msg": "출고 처리 완료"}

    if t == "MOVE":
        move_inventory(p.warehouse, p.item_code, p.item_name, p.brand, p.lot_no, p.spec, abs(qty), p.from_location, p.to_location)
        return {"ok": True, "msg": "이동 처리 완료"}

    return {"ok": False, "msg": "알 수 없는 type"}
