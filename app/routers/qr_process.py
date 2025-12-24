from fastapi import APIRouter
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from app.db import add_inventory, subtract_inventory, move_inventory

router = APIRouter(prefix="/api/qr", tags=["QR 처리"])

class QRBody(BaseModel):
    action: str  # IN/OUT/MOVE
    warehouse: str = "MAIN"
    location: str = ""
    from_location: str = ""
    to_location: str = ""
    brand: str = ""
    item_code: str
    item_name: str = ""
    lot_no: str
    spec: str = ""
    qty: float

@router.post("/process")
def qr_process(body: QRBody):
    try:
        act = body.action.upper().strip()
        if act == "IN":
            add_inventory(body.warehouse, body.location, body.brand, body.item_code, body.item_name, body.lot_no, body.spec, float(body.qty), remark="QR 입고")
        elif act == "OUT":
            subtract_inventory(body.warehouse, body.location, body.item_code, body.lot_no, float(body.qty), remark="QR 출고", block_negative=True)
        elif act == "MOVE":
            move_inventory(body.warehouse, body.item_code, body.lot_no, body.from_location, body.to_location, float(body.qty), remark="QR 이동", block_negative=True)
        else:
            return JSONResponse({"ok": False, "detail": "action은 IN/OUT/MOVE"}, status_code=400)

        return {"ok": True}
    except Exception as e:
        return JSONResponse({"ok": False, "detail": str(e)}, status_code=400)
