# ==================================================
# IMPORTS
# ==================================================
from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse

from app.db import subtract_inventory


# ==================================================
# ROUTER SETUP
# ==================================================
router = APIRouter(
    prefix="/api/outbound",
    tags=["Outbound"]
)


# ==================================================
# OUTBOUND API
# ==================================================
@router.post("")
def outbound_item(
    item_code: str = Form(...),        # 품목코드
    location_code: str = Form(...),    # 로케이션
    lot: str = Form(...),              # LOT
    quantity: int = Form(...)          # 출고 수량
):
    """
    출고 처리 API
    - 재고 존재 여부 확인
    - 수량 부족 시 에러 반환
    """

    try:
        # ------------------------------
        # 출고 처리
        # ------------------------------
        subtract_inventory(
            item_code=item_code,
            location_code=location_code,
            lot=lot,
            quantity=quantity
        )

        return {"result": "OK"}

    except ValueError as e:
        # ------------------------------
        # 업무 에러 (재고 없음, 수량 부족 등)
        # ------------------------------
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )
