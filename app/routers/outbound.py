from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import RedirectResponse
from app.db import subtract_inventory

router = APIRouter(prefix="/api/outbound", tags=["출고"])

@router.post("/manual")
def outbound_manual(
    warehouse: str = Form("MAIN"),
    location: str = Form(""),
    item_code: str = Form(...),
    lot_no: str = Form(""),
    qty: float = Form(...),
    next_url: str = Form("/inventory-page")
):
    try:
        subtract_inventory(warehouse, location, item_code, lot_no, qty, remark="수기 출고")
        return RedirectResponse(next_url, status_code=303)
    except Exception as e:
        raise HTTPException(400, str(e))
