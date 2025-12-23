# app/routers/outbound.py
from fastapi import APIRouter, HTTPException
from app.db import subtract_inventory, log_history

router = APIRouter(prefix="/api/outbound")

@router.get("/manual")
def outbound_manual(
    item_code: str,
    lot_no: str,
    location: str,
    qty: float,
    warehouse: str = "MAIN"
):
    try:
        subtract_inventory(warehouse, location, item_code, lot_no, qty)
    except Exception as e:
        raise HTTPException(400, str(e))

    log_history("OUT", warehouse, location, item_code, lot_no, qty, "수동출고")
    return {"result": "OK"}
