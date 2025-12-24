from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
from app.db import subtract_inventory

router = APIRouter(prefix="/api/outbound", tags=["outbound"])

@router.post("/manual")
def outbound_manual(
    warehouse: str = Form("MAIN"),
    location: str = Form(...),
    item_code: str = Form(...),
    lot_no: str = Form(...),
    qty: float = Form(...),
):
    subtract_inventory(warehouse, location, item_code, lot_no, qty, remark="MANUAL OUT")
    return RedirectResponse(url="/inventory-page", status_code=303)
