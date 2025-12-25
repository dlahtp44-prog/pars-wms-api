from fastapi import APIRouter, Form, HTTPException
from app.db import subtract_inventory

router = APIRouter(prefix="/api/outbound", tags=["Outbound"])

@router.post("/manual")
def outbound_manual(
    warehouse: str = Form(...),
    location: str = Form(...),
    item_code: str = Form(...),
    qty: float = Form(...),
    lot_no: str = Form("")
):
    ok = subtract_inventory(
        warehouse=warehouse,
        location=location,
        item_code=item_code,
        lot_no=lot_no,
        qty=qty
    )
    if not ok:
        raise HTTPException(status_code=400, detail="재고 부족")
    return {"result": "OK"}
