from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import RedirectResponse
from app.db import subtract_inventory, log_history

router = APIRouter(prefix="/api/outbound", tags=["출고"])

@router.post("/manual")
def outbound_manual(
    warehouse: str = Form("MAIN"),
    location: str = Form(...),
    item_code: str = Form(...),
    lot_no: str = Form(...),
    qty: float = Form(...),
):
    try:
        subtract_inventory(warehouse, location, item_code, lot_no, qty, block_negative=True)
    except ValueError as e:
        raise HTTPException(400, str(e))

    log_history("OUT", warehouse, location, item_code, lot_no, qty, "수동 출고")
    return RedirectResponse(url="/inventory-page", status_code=303)
