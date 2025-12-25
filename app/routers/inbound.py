from fastapi import APIRouter
from app.db import add_inventory

router = APIRouter(prefix="/api/inbound", tags=["Inbound"])


@router.post("")
def inbound_item(
    item_code: str,
    item_name: str,
    brand: str,
    spec: str,
    location_code: str,
    lot: str,
    quantity: int
):
    add_inventory(
        item_code=item_code,
        item_name=item_name,
        brand=brand,
        spec=spec,
        location_code=location_code,
        lot=lot,
        quantity=quantity
    )
    return {"result": "OK"}
