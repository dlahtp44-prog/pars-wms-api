from fastapi import APIRouter, HTTPException
from app.db import subtract_inventory

router = APIRouter(prefix="/api/outbound", tags=["출고"])

@router.post("")
def outbound(
    warehouse: str,
    location: str,
    item_code: str,
    lot_no: str,
    qty: float
):
    try:
        subtract_inventory(warehouse, location, item_code, lot_no, qty)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return {"result": "OK", "msg": "출고 완료"}
