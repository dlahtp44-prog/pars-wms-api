# ==================================================
# IMPORTS
# ==================================================
from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse

from app.db import add_inventory


# ==================================================
# ROUTER SETUP
# ==================================================
router = APIRouter(
    prefix="/api/inbound",
    tags=["Inbound"]
)


# ==================================================
# INBOUND API
# ==================================================
@router.post("")
def inbound_item(
    item_code: str = Form(...),        # 품목코드
    item_name: str = Form(...),        # 제품명
    brand: str = Form(...),            # 브랜드
    spec: str = Form(...),             # 규격
    location_code: str = Form(...),    # 로케이션
    lot: str = Form(...),              # LOT
    quantity: int = Form(...)          # 입고 수량
):
    """
    입고 처리 API
    - 신규 품목 자동 등록
    - 재고 증가
    - 이력 기록
    """

    try:
        # ------------------------------
        # 입고 처리
        # ------------------------------
        add_inventory(
            item_code=item_code,
            item_name=item_name,
            brand=brand,
            spec=spec,
            location_code=location_code,
            lot=lot,
            quantity=quantity
        )

        return {"result": "OK"}

    except Exception as e:
        # ------------------------------
        # 예외 처리 (DB / 로직 오류)
        # ------------------------------
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
