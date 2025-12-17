from fastapi import APIRouter
from app.db import get_conn

router = APIRouter(tags=["재고"])

@router.get("/inventory")
def inventory():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT warehouse, location, brand, item, name, lot, spec, qty
        FROM inventory
    """)
    rows = cur.fetchall()
    conn.close()

    return {
        "재고목록": [
            {
                "장소명": r[0],
                "로케이션": r[1],
                "브랜드": r[2],
                "품번": r[3],
                "품명": r[4],
                "LOT": r[5],
                "규격": r[6],
                "현재고": r[7]
            } for r in rows
        ]
    }
