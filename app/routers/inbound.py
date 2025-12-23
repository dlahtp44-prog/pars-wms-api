from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import RedirectResponse
from app.db import add_inventory

router = APIRouter(prefix="/api/inbound", tags=["입고"])

@router.post("/manual")
def inbound_manual(
    warehouse: str = Form("MAIN"),
    location: str = Form(""),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(""),
    lot_no: str = Form(""),
    spec: str = Form(""),
    qty: float = Form(...),
    next_url: str = Form("/inventory-page")
):
    try:
        add_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, qty, remark="수기 입고")
        return RedirectResponse(next_url, status_code=303)
    except Exception as e:
        raise HTTPException(400, str(e))
