# app/routers/move.py 수정본

from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.db import move_inventory

# prefix는 그대로 유지
router = APIRouter(prefix="/api/move")

# 경로를 "" 에서 "/manual" 로 수정합니다.
@router.post("/manual")
async def move_process(
    warehouse: str = Form("기본창고"),
    from_location: str = Form(...),
    to_location: str = Form(...),
    item_code: str = Form(...),
    lot_no: str = Form(""),
    qty: float = Form(...)
):
    try:
        # db.py의 move_inventory 호출
        move_inventory(warehouse, from_location, to_location, item_code, lot_no, qty)
        return JSONResponse({"status": "success", "message": "이동 완료"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
