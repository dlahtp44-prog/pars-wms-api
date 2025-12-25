# app/routers/move.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db import move_inventory

router = APIRouter(prefix="/api/move", tags=["이동"])

class MoveBody(BaseModel):
    warehouse: str = "MAIN"
    item_code: str
    lot_no: str
    qty: float
    from_location: str
    to_location: str

@router.post("/manual")
def move_manual(body: MoveBody):
    try:
        move_inventory(
            body.warehouse,
            body.item_code,
            body.lot_no,
            body.qty,
            body.from_location,
            body.to_location,
            remark="QR 이동"
        )
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
