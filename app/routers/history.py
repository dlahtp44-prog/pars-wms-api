from fastapi import APIRouter
from app.db import get_conn

router = APIRouter(tags=["이력"])

@router.get("/api/history", summary="작업 이력 조회")
def history_list():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT type, warehouse, brand, item_code, item_name,
               lot_no, spec, location, qty, created_at
        FROM history
        ORDER BY created_at DESC
    """)
    rows = cur.fetchall()
    conn.close()

    return {
        "작업이력": [
            {
                "구분": r[0],
                "장소명": r[1],
                "브랜드": r[2],
                "품번": r[3],
                "품명": r[4],
                "LOT": r[5],
                "규격": r[6],
                "로케이션": r[7],
                "수량": r[8],
                "일시": r[9],
            }
            for r in rows
        ]
    }
