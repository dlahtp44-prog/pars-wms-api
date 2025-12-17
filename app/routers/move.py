from fastapi import APIRouter
from app.db import log_history

router = APIRouter(tags=["재고이동"])

@router.post("/move", summary="재고 이동")
def move(item: str, qty: int, from_loc: str, to_loc: str):
    remark = f"{from_loc} → {to_loc}"

    # ✅ 실제 수량 변화 없음 (이동 로그만)
    log_history("이동", item, qty, remark)

    return {
        "결과": "재고 이동 완료",
        "이동경로": remark
    }
