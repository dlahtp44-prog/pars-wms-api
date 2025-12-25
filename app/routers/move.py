# app/routers/move.py
from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
from app.db import move_inventory

router = APIRouter(prefix="/api/move", tags=["move"])

@router.post("/manual")
def move_manual(
    warehouse: str = Form("MAIN"),
    from_location: str = Form(...),
    to_location: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(""),
    lot_no: str = Form(...),
    spec: str = Form(""),
    qty: float = Form(...),
):
    move_inventory(warehouse, from_location, to_location, brand, item_code, item_name, lot_no, spec, qty, remark="수동이동", block_negative=True)
    return RedirectResponse("/inventory-page", status_code=303)
