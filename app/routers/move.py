# app/routers/move.py
from fastapi import APIRouter, HTTPException
from app.db import subtract_inventory, add_inventory, log_history

router = APIRouter(prefix="/api/move")

@router.get("")
def move(
    item_code: str,
    lot_no: str,
    from_location: str,
    to_location: str,
    qty: float,
    warehouse: str = "MAIN"
):
    try:
        subtract_inventory(warehouse, from_location, item_code, lot_no, qty)
        add_inventory(warehouse, to_location, item_code, "", lot_no, "", qty)
    except Exception as e:
        raise HTTPException(400, str(e))

    log_history("MOVE", warehouse, from_location, item_code, lot_no, qty, f"→ {to_location}")
    return {"result": "OK"}
