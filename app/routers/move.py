from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db import move_inventory

router = APIRouter(prefix="/api/move", tags=["이동"])

class MoveReq(BaseModel):
    warehouse: str = "MAIN"
    item_code: str
    lot_no: str
    qty: float
    from_location: str
    to_location: str

@router.post("")
def move(req: MoveReq):
    try:
        move_inventory(req.warehouse, req.item_code, req.lot_no, req.qty, req.from_location, req.to_location, remark="MOVE")
        return {"ok": True}
    except Exception as e:
        raise HTTPException(400, str(e))
