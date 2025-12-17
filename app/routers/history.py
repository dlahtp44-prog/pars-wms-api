from fastapi import APIRouter
from app.db import get_conn

router = APIRouter(tags=["이력"])

@router.get("/api/history")
def history():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT type, item, qty, warehouse, location, remark, created_at
        FROM history ORDER BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()

    return {
        "작업이력": [
            {
                "작업유형": r[0],
                "품번": r[1],
                "수량": r[2],
                "장소명": r[3],
                "로케이션": r[4],
                "비고": r[5],
                "일시": r[6]
            } for r in rows
        ]
    }
