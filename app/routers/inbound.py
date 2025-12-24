from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
from app.db import add_inventory, log_history

router = APIRouter(prefix="/api/inbound", tags=["입고"])

@router.post("/manual")
def inbound_manual(
    warehouse: str = Form("MAIN"),
    location: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(""),
    lot_no: str = Form(...),
    spec: str = Form(""),
    qty: float = Form(...)
):
    add_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, qty)
    log_history("IN", warehouse, location, item_code, lot_no, qty, "수동 입고")
    return RedirectResponse(url="/inventory-page", status_code=303)
