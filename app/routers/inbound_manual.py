from fastapi import APIRouter, Form
from app.db import add_inventory

router = APIRouter(prefix="/api/inbound")

@router.post("/manual")
def inbound_manual(
    warehouse: str = Form("MAIN"),
    location: str = Form(...),
    item_code: str = Form(...),
    lot_no: str = Form(""),
    item_name: str = Form(""),
    spec: str = Form(""),
    qty: float = Form(...)
):
    add_inventory(
        warehouse, location, "", item_code, item_name, lot_no, spec, qty
    )
    return {"result": "OK"}
