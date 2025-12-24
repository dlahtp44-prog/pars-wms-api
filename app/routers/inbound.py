from fastapi import APIRouter, Request, Form
from fastapi.responses import JSONResponse
from app.db import add_inventory

router = APIRouter(prefix="/api/inbound")

@router.post("/manual")
async def inbound_manual(
    warehouse: str = Form("기본창고"),
    location: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(""),
    lot_no: str = Form(""),
    spec: str = Form(""),
    qty: float = Form(...),
    remark: str = Form("")
):
    try:
        add_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, qty, remark)
        return JSONResponse({"status": "success", "message": "입고 완료"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
