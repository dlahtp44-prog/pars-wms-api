from fastapi import APIRouter, Form
from app.db import move_inventory

router = APIRouter(prefix="/api/move")

@router.post("")
def move(
    warehouse: str = Form("MAIN"),
    from_location: str = Form(...),
    to_location: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(""),
    lot_no: str = Form(...),
    spec: str = Form(""),
    qty: float = Form(...)
):
    move_inventory(
        warehouse,
        from_location,
        to_location,
        brand,
        item_code,
        item_name,
        lot_no,
        spec,
        qty
    )
    return {"result": "OK"}
