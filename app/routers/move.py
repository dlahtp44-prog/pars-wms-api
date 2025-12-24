from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.db import move_inventory

# prefix가 /api/move 이므로
router = APIRouter(prefix="/api/move")

# 경로를 /manual로 설정하여 프론트엔드의 요청 주소(/api/move/manual)와 일치시킵니다.
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
        # db.py의 move_inventory 함수 호출
        move_inventory(warehouse, from_location, to_location, item_code, lot_no, qty)
        return JSONResponse({"status": "success", "message": "이동 완료"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
