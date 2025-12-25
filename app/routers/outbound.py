# app/routers/outbound.py
from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
from app.db import subtract_inventory

router = APIRouter(prefix="/api/outbound", tags=["outbound"])

@router.post("/manual")
def outbound_manual(
    warehouse: str = Form("MAIN"),
    location: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(""),
    lot_no: str = Form(...),
    spec: str = Form(""),
    qty: float = Form(...),
):
    subtract_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, qty, remark="수동출고", block_negative=True)
    return RedirectResponse("/inventory-page", status_code=303)
