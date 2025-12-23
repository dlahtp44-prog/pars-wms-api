from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db import add_inventory, subtract_inventory, move_inventory

router = APIRouter(prefix="/api/qr", tags=["QR"])

class QRBody(BaseModel):
    action: str  # IN / OUT / MOVE
    warehouse: str = "MAIN"
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
def process_qr(body: QRBody):
    try:
        act = body.action.upper().strip()
        if act == "IN":
            add_inventory(body.warehouse, body.location, body.brand, body.item_code, body.item_name, body.lot_no, body.spec, body.qty, remark="QR 입고")
        elif act == "OUT":
            subtract_inventory(body.warehouse, body.location, body.item_code, body.lot_no, body.qty, remark="QR 출고",
                               brand=body.brand, item_name=body.item_name, spec=body.spec)
        elif act == "MOVE":
            move_inventory(body.warehouse, body.from_location, body.to_location, body.brand, body.item_code, body.item_name, body.lot_no, body.spec, body.qty, remark="QR 이동")
        else:
            raise ValueError("action은 IN/OUT/MOVE만 허용")
        return {"ok": True}
    except Exception as e:
        raise HTTPException(400, str(e))
