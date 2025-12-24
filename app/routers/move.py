from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse, JSONResponse
from app.db import move_inventory

router = APIRouter(prefix="/api/move", tags=["이동"])

@router.post("/manual")
def move_manual(
    warehouse: str = Form("MAIN"),
    item_code: str = Form(...),
    lot_no: str = Form(...),
    from_location: str = Form(...),
    to_location: str = Form(...),
    qty: float = Form(0)
):
    try:
        move_inventory(warehouse, item_code, lot_no, from_location, to_location, float(qty), remark="수동 이동", block_negative=True)
        return RedirectResponse(url="/inventory-page", status_code=303)
    except Exception as e:
        return JSONResponse({"ok": False, "detail": str(e)}, status_code=400)
