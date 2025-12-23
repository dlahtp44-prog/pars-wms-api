from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db import add_inventory, subtract_inventory, move_inventory

router = APIRouter(prefix="/api/qr", tags=["QR Process"])

class QRProcess(BaseModel):
    action: str  # IN/OUT/MOVE
    warehouse: str = "MAIN"
    location: str = ""         # IN/OUT
    from_location: str = ""    # MOVE
    to_location: str = ""      # MOVE
    brand: str = ""
    item_code: str
    item_name: str = ""
    lot_no: str
    spec: str = ""
    qty: float

@router.post("/process")
def qr_process(body: QRProcess):
    try:
        if body.action == "IN":
            add_inventory(body.warehouse, body.location, body.brand, body.item_code, body.item_name, body.lot_no, body.spec, body.qty, remark="QR IN")
        elif body.action == "OUT":
            subtract_inventory(body.warehouse, body.location, body.item_code, body.lot_no, body.qty, remark="QR OUT")
        elif body.action == "MOVE":
            move_inventory(body.warehouse, body.item_code, body.lot_no, body.qty, body.from_location, body.to_location, remark="QR MOVE")
        else:
            raise ValueError("action must be IN/OUT/MOVE")
        return {"ok": True}
    except Exception as e:
        raise HTTPException(400, str(e))
