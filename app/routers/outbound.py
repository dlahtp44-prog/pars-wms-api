from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse, JSONResponse
from app.db import subtract_inventory

router = APIRouter(prefix="/api/outbound", tags=["출고"])

@router.post("/manual")
def outbound_manual(
    warehouse: str = Form("MAIN"),
    location: str = Form(...),
    item_code: str = Form(...),
    lot_no: str = Form(...),
    qty: float = Form(0)
):
    try:
        subtract_inventory(warehouse, location, item_code, lot_no, float(qty), remark="수동 출고", block_negative=True)
        return RedirectResponse(url="/inventory-page", status_code=303)
    except Exception as e:
        return JSONResponse({"ok": False, "detail": str(e)}, status_code=400)
