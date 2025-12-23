# app/routers/inbound.py
from fastapi import APIRouter
from app.db import add_inventory, log_history

router = APIRouter(prefix="/api/inbound")

@router.get("/manual")
def inbound_manual(
    item_code: str,
    item_name: str = "",
    spec: str = "",
    lot_no: str = "",
    location: str = "",
    qty: float = 0,
    warehouse: str = "MAIN"
):
    add_inventory(warehouse, location, item_code, item_name, lot_no, spec, qty)
    log_history("IN", warehouse, location, item_code, lot_no, qty, "수동입고")
    return {"result": "OK"}
