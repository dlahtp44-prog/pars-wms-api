from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import RedirectResponse
from app.db import move_inventory, log_history

router = APIRouter(prefix="/api/move", tags=["이동"])

@router.post("/manual")
def move_manual(
    warehouse: str = Form("MAIN"),
    from_location: str = Form(...),
    to_location: str = Form(...),
    item_code: str = Form(...),
    lot_no: str = Form(...),
    qty: float = Form(...),
):
    try:
        move_inventory(warehouse, from_location, to_location, item_code, lot_no, qty, block_negative=True)
    except ValueError as e:
        raise HTTPException(400, str(e))

    log_history("MOVE", warehouse, f"{from_location}→{to_location}", item_code, lot_no, qty, "수동 이동")
    return RedirectResponse(url="/inventory-page", status_code=303)
