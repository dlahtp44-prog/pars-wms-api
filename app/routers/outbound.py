from fastapi import APIRouter
from app.db import subtract_inventory

router = APIRouter(prefix="/api/outbound", tags=["Outbound"])


@router.post("")
def outbound_item(
    item_code: str,
    location_code: str,
    lot: str,
    quantity: int
):
    subtract_inventory(
        item_code=item_code,
        location_code=location_code,
        lot=lot,
        quantity=quantity
    )
    return {"result": "OK"}
