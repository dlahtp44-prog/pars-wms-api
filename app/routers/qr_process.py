from fastapi import APIRouter
from pydantic import BaseModel
from app.db import add_inventory, subtract_inventory, move_inventory

router = APIRouter(prefix="/api/qr/process")

class QRBody(BaseModel):
    action: str
    warehouse: str = "MAIN"
    location: str = ""
    from_location: str = ""
    to_location: str = ""
    item_code: str
    item_name: str = ""
    lot_no: str
    spec: str = ""
    brand: str = ""
    qty: float

@router.post("")
def process(body: QRBody):
    if body.action == "IN":
        add_inventory(
            body.warehouse, body.location, body.brand,
            body.item_code, body.item_name,
            body.lot_no, body.spec, body.qty
        )
    elif body.action == "OUT":
        subtract_inventory(
            body.warehouse, body.location, body.brand,
            body.item_code, body.item_name,
            body.lot_no, body.spec, body.qty
        )
    elif body.action == "MOVE":
        move_inventory(
            body.warehouse,
            body.from_location,
            body.to_location,
            body.brand,
            body.item_code,
            body.item_name,
            body.lot_no,
            body.spec,
            body.qty
        )
    else:
        raise ValueError("Invalid action")

    return {"result": "OK"}
