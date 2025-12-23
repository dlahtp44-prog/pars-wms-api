from fastapi import APIRouter
from pydantic import BaseModel
from app.db import add_inventory

router = APIRouter(prefix="/api/inbound", tags=["입고"])

class InboundReq(BaseModel):
    warehouse: str = "MAIN"
    location: str
    brand: str = ""
    item_code: str
    item_name: str = ""
    lot_no: str
    spec: str = ""
    qty: float

@router.post("")
def inbound(req: InboundReq):
    add_inventory(req.warehouse, req.location, req.brand, req.item_code, req.item_name, req.lot_no, req.spec, req.qty, remark="INBOUND")
    return {"ok": True}
