from fastapi import APIRouter
from app.db import move_inventory

router = APIRouter(prefix="/api/move", tags=["Move"])


@router.post("")
def move_item(
    item_code: str,
    lot: str,
    location_from: str,
    location_to: str,
    quantity: int
):
    move_inventory(
        item_code=item_code,
        lot=lot,
        location_from=location_from,
        location_to=location_to,
        quantity=quantity
    )
    return {"result": "OK"}
