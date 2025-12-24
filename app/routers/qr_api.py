from fastapi import APIRouter, HTTPException
from app.db import get_location_items, move_inventory
from pydantic import BaseModel

router = APIRouter(prefix="/api/qr", tags=["QR"])

class MoveRequest(BaseModel):
    warehouse: str = "기본창고"
    from_location: str
    to_location: str
    item_code: str
    lot_no: str
    qty: float

@router.get("/location/{loc}")
async def qr_location_view(loc: str):
    items = get_location_items(loc)
    return items

@router.post("/move")
async def qr_move_process(req: MoveRequest):
    try:
        move_inventory(req.warehouse, req.from_location, req.to_location, req.item_code, req.lot_no, req.qty)
        return {"status": "success", "message": "이동 완료"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
