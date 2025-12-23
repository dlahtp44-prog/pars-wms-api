from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import RedirectResponse
from app.db import move_inventory

router = APIRouter(prefix="/api/move", tags=["이동"])

@router.post("/manual")
def move_manual(
    warehouse: str = Form("MAIN"),
    from_location: str = Form(...),
    to_location: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(""),
    lot_no: str = Form(""),
    spec: str = Form(""),
    qty: float = Form(...),
    next_url: str = Form("/inventory-page")
):
    try:
        move_inventory(warehouse, from_location, to_location, brand, item_code, item_name, lot_no, spec, qty, remark="수기 이동")
        return RedirectResponse(next_url, status_code=303)
    except Exception as e:
        raise HTTPException(400, str(e))
