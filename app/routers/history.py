from fastapi import APIRouter
from app.db import get_conn

router = APIRouter(tags=["이력"])

@router.get("/api/history", summary="작업 이력 조회")
def history():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT type, item, qty, location, remark, created_at
        FROM history
        ORDER BY id DESC
    """)
    rows = cur.fetchall()

    conn.close()

    return {
        "작업이력": [
            {
                "구분": r[0],
                "품목": r[1],
                "수량": r[2],
                "위치": r[3],
                "비고": r[4],
                "시간": r[5]
            } for r in rows
        ]
    }
