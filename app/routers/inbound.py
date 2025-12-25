from fastapi import APIRouter, Form
from app.db import add_inventory

router = APIRouter(prefix="/api/inbound", tags=["Inbound"])

@router.post("/manual")
def inbound_manual(
    warehouse: str = Form(...),
    location: str = Form(...),
    item_code: str = Form(...),
    qty: float = Form(...),
    item_name: str = Form(""),
    lot_no: str = Form(""),
    spec: str = Form(""),
    brand: str = Form("")
):
    add_inventory(
        warehouse=warehouse,
        location=location,
        item_code=item_code,
        item_name=item_name,
        lot_no=lot_no,
        spec=spec,
        brand=brand,
        qty=qty
    )
    return {"result": "OK"}
