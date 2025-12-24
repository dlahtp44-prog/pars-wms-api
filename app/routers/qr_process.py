from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db import add_inventory, subtract_inventory, move_inventory, log_history

router = APIRouter(prefix="/api/qr", tags=["QR"])

class QRBody(BaseModel):
    action: str  # IN / OUT / MOVE / LOC
    warehouse: str = "MAIN"
    location: str = ""
    from_location: str = ""
    to_location: str = ""
    brand: str = ""
    item_code: str = ""
    item_name: str = ""
    lot_no: str = ""
    spec: str = ""
    qty: float = 0.0

@router.post("/process")
def qr_process(body: QRBody):
    a = (body.action or "").upper().strip()

    if a == "IN":
        if not body.location or not body.item_code or not body.lot_no:
            raise HTTPException(400, "IN: location/item_code/lot_no 필수")
        add_inventory(body.warehouse, body.location, body.brand, body.item_code, body.item_name, body.lot_no, body.spec, body.qty)
        log_history("IN", body.warehouse, body.location, body.item_code, body.lot_no, body.qty, "QR 입고")
        return {"ok": True}

    if a == "OUT":
        if not body.location or not body.item_code or not body.lot_no:
            raise HTTPException(400, "OUT: location/item_code/lot_no 필수")
        try:
            subtract_inventory(body.warehouse, body.location, body.item_code, body.lot_no, body.qty, block_negative=True)
        except ValueError as e:
            raise HTTPException(400, str(e))
        log_history("OUT", body.warehouse, body.location, body.item_code, body.lot_no, body.qty, "QR 출고")
        return {"ok": True}

    if a == "MOVE":
        if not body.from_location or not body.to_location or not body.item_code or not body.lot_no:
            raise HTTPException(400, "MOVE: from_location/to_location/item_code/lot_no 필수")
        try:
            move_inventory(body.warehouse, body.from_location, body.to_location, body.item_code, body.lot_no, body.qty, block_negative=True)
        except ValueError as e:
            raise HTTPException(400, str(e))
        log_history("MOVE", body.warehouse, f"{body.from_location}→{body.to_location}", body.item_code, body.lot_no, body.qty, "QR 이동")
        return {"ok": True}

    raise HTTPException(400, f"지원하지 않는 action: {a}")
