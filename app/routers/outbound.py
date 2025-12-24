from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.db import subtract_inventory

router = APIRouter(prefix="/api/outbound")

@router.post("/manual")
async def outbound_manual(
    warehouse: str = Form("기본창고"),
    location: str = Form(...),
    item_code: str = Form(...),
    lot_no: str = Form(""),
    qty: float = Form(...),
    remark: str = Form("")
):
    try:
        subtract_inventory(warehouse, location, item_code, lot_no, qty, remark)
        return JSONResponse({"status": "success", "message": "출고 완료"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
