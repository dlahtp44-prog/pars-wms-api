from fastapi import APIRouter, Form
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
    add_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, qty, remark="MANUAL IN")
    # 작업자 화면에서 제출하면 바로 재고로 보이게 이동
    return RedirectResponse(url="/inventory-page", status_code=303)
