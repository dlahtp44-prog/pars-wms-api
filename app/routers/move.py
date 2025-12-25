from fastapi import APIRouter, Form
from app.db import move_inventory

router = APIRouter(prefix="/api/move", tags=["Move"])


@router.post("")
def move_item(
    item_code: str = Form(...),
    lot: str = Form(...),
    location_from: str = Form(...),
    location_to: str = Form(...),
    quantity: int = Form(...)
):
    move_inventory(
        item_code=item_code,
        lot=lot,
        location_from=location_from,
        location_to=location_to,
        quantity=quantity
    )
    return {"result": "OK"}
