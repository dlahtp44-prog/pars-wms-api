# app/routers/outbound.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db import subtract_inventory

router = APIRouter(prefix="/api/outbound", tags=["출고"])

class OutBody(BaseModel):
    warehouse: str = "MAIN"
    location: str
    brand: str = ""
    item_code: str
    item_name: str = ""
    lot_no: str = ""
    spec: str = ""
    qty: float

@router.post("/manual")
def outbound_manual(body: OutBody):
    try:
        subtract_inventory(
            body.warehouse, body.location, body.brand,
            body.item_code, body.item_name, body.lot_no, body.spec, body.qty,
            remark="수동/QR 출고",
            block_negative=True
        )
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
