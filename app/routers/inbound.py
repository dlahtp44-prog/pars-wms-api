from fastapi import APIRouter, Form
from app.db import add_inventory

router = APIRouter(prefix="/api/inbound", tags=["Inbound"])


@router.post("")
def inbound_item(
    item_code: str = Form(...),
    item_name: str = Form(...),
    brand: str = Form(...),
    spec: str = Form(...),
    location_code: str = Form(...),
    lot: str = Form(...),
    quantity: int = Form(...)
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
