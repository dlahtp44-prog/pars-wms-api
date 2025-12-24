from fastapi import APIRouter, HTTPException
from app import db

router = APIRouter(prefix="/api/qr", tags=["QR API"])

@router.get("/location/{location_id}")
async def read_location(location_id: str):
    items = db.get_location_items(location_id)
    return items

@router.post("/move")
async def qr_move(data: dict):
    try:
        db.move_inventory(
            warehouse=data.get("warehouse", "MAIN"),
            from_loc=data["from_location"],
            to_loc=data["to_location"],
            item_code=data["item_code"],
            lot_no=data["lot_no"],
            qty=float(data["qty"]),
            remark="QR 이동"
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
