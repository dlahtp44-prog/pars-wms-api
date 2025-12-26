from fastapi import APIRouter
from app.db import get_inventory, get_history

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("")
def dashboard():
    """
    대시보드 요약
    - 총 재고 수량
    - 입고/출고/이동 건수
    """
    inventory = get_inventory()
    history = get_history()

    total_inventory = sum(r["quantity"] for r in inventory)

    inbound_cnt = sum(1 for r in history if r["action"] == "INBOUND")
    outbound_cnt = sum(1 for r in history if r["action"] == "OUTBOUND")
    move_cnt = sum(1 for r in history if r["action"] == "MOVE")

    return {
        "total_inventory": total_inventory,
        "inbound_count": inbound_cnt,
        "outbound_count": outbound_cnt,
        "move_count": move_cnt
    }
