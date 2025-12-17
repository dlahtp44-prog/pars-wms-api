from fastapi import APIRouter
from app.db import get_conn

router = APIRouter(tags=["재고"])

@router.get(
    "/inventory",
    summary="재고 현황 조회",
    description="현재 전체 재고 현황을 조회합니다."
)
def inventory():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT item, qty, location FROM inventory")
    rows = cur.fetchall()

    conn.close()

    return {
        "재고목록": [
            {"품목": r[0], "수량": r[1], "위치": r[2]} for r in rows
        ]
    }
