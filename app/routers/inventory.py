from fastapi import APIRouter
import sqlite3

router = APIRouter(
    prefix="/inventory",
    tags=["재고"]
)

DB_PATH = "WMS.db"


def get_db():
    return sqlite3.connect(DB_PATH)


@router.get(
    "",
    summary="재고 현황 조회",
    description="현재 품목별 · 위치별 재고 현황을 조회합니다."
)
def inventory_list():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT item_code, location, qty
        FROM inventory
        ORDER BY item_code, location
    """)

    rows = cur.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "품목코드": r[0],
            "로케이션": r[1],
            "수량": r[2]
        })

    return {
        "재고건수": len(result),
        "재고목록": result
    }
