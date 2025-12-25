# app/routers/inbound.py
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from app.db import add_inventory

router = APIRouter(prefix="/api/inbound", tags=["inbound"])

@router.post("/manual")
def inbound_manual(
    warehouse: str = Form("MAIN"),
    location: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(""),
    lot_no: str = Form(...),
    spec: str = Form(""),
    qty: float = Form(...),
):
    add_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, qty, remark="수동입고")
    return RedirectResponse("/inventory-page", status_code=303)
