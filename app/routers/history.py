from fastapi import APIRouter
from app.db import get_conn

router = APIRouter(tags=["이력"])

@router.get(
    "/api/history",
    summary="작업 이력 조회",
    description="입고, 출고, 이동 작업 이력을 조회합니다."
)
def history():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT type, item, qty, memo, created_at FROM history ORDER BY created_at DESC"
    )
    rows = cur.fetchall()
    conn.close()

    return {
        "작업이력": [
            {
                "유형": r[0],
                "품목": r[1],
                "수량": r[2],
                "메모": r[3],
                "시간": r[4]
            }
            for r in rows
        ]
    }
