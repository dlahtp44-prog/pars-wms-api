from fastapi import APIRouter, Form
from app.db import move_inventory

router = APIRouter(prefix="/api/move")

@router.post("/manual")
def move_manual(
    warehouse: str = Form("MAIN"),
    item_code: str = Form(...),
    lot_no: str = Form(""),
    from_location: str = Form(...),
    to_location: str = Form(...),
    qty: float = Form(...)
):
    move_inventory(
        warehouse, item_code, lot_no, from_location, to_location, qty
    )
    return {"result": "OK"}
