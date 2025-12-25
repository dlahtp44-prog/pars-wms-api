# app/routers/inbound.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db import add_inventory

router = APIRouter(prefix="/api/inbound", tags=["입고"])

class InboundBody(BaseModel):
    warehouse: str = "MAIN"
    location: str
    brand: str = ""
    item_code: str
    item_name: str = ""
    lot_no: str = ""
    spec: str = ""
    qty: float

@router.post("/manual")
def inbound_manual(body: InboundBody):
    try:
        add_inventory(
            body.warehouse, body.location, body.brand,
            body.item_code, body.item_name, body.lot_no, body.spec, body.qty,
            remark="수동/QR 입고"
        )
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
