from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse, JSONResponse
from app.db import add_inventory

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
    qty: float = Form(0)
):
    try:
        add_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, float(qty), remark="수동 입고")
        return RedirectResponse(url="/inventory-page", status_code=303)
    except Exception as e:
        return JSONResponse({"ok": False, "detail": str(e)}, status_code=400)

# QR/GET 방식도 같이 지원 (QR이 querystring 형태일 때)
@router.get("/manual")
def inbound_manual_get(
    warehouse: str = "MAIN",
    location: str = "",
    brand: str = "",
    item_code: str = "",
    item_name: str = "",
    lot_no: str = "",
    spec: str = "",
    qty: float = 0
):
    add_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, float(qty), remark="QR/GET 입고")
    return {"ok": True}
