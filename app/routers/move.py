from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
from app.db import move_inventory

router = APIRouter(prefix="/api/move", tags=["move"])

@router.post("/manual")
def move_manual(
    warehouse: str = Form("MAIN"),
    from_location: str = Form(...),
    to_location: str = Form(...),
    item_code: str = Form(...),
    lot_no: str = Form(...),
    qty: float = Form(...),
):
    move_inventory(warehouse, from_location, to_location, item_code, lot_no, qty, remark="MANUAL MOVE")
    return RedirectResponse(url="/inventory-page", status_code=303)
