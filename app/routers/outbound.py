from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db import subtract_inventory

router = APIRouter(prefix="/api/outbound", tags=["출고"])

class OutboundReq(BaseModel):
    warehouse: str = "MAIN"
    location: str
    item_code: str
    lot_no: str
    qty: float

@router.post("")
def outbound(req: OutboundReq):
    try:
        subtract_inventory(req.warehouse, req.location, req.item_code, req.lot_no, req.qty, remark="OUTBOUND")
        return {"ok": True}
    except Exception as e:
        raise HTTPException(400, str(e))
