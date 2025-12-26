from fastapi import APIRouter, Query
from app.db import get_history

router = APIRouter(prefix="/api/report", tags=["Report"])

@router.get("")
def report(
    action: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None)
):
    """
    통합 리포트
    - action: INBOUND | OUTBOUND | MOVE | None
    - 날짜는 YYYY-MM-DD
    """
    rows = get_history(
        action=action,
        start_date=start_date,
        end_date=end_date
    )
    return rows
