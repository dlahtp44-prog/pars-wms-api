from fastapi import APIRouter, HTTPException
from app.db import subtract_inventory, add_inventory, log_history

router = APIRouter(prefix="/api/move", tags=["이동"])

@router.post("")
def move(
    warehouse: str,
    from_location: str,
    to_location: str,
    item_code: str,
    lot_no: str,
    qty: float
):
    try:
        subtract_inventory(warehouse, from_location, item_code, lot_no, qty)
        add_inventory(
            warehouse, to_location, "",
            item_code, "", lot_no, "", qty
        )
        log_history(
            "MOVE",
            warehouse,
            f"{from_location}->{to_location}",
            item_code,
            lot_no,
            qty,
            "이동"
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    return {"result": "OK", "msg": "이동 완료"}
