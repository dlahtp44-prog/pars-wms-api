from fastapi import APIRouter
from app.db import get_conn

router = APIRouter(tags=["재고"])

@router.get("/inventory", summary="재고 현황 조회")
def inventory(warehouse: str | None = None, q: str | None = None):
    """
    - warehouse: 창고 필터 (예: A창고)
    - q: 검색어 (품번/품명/브랜드/LOT/로케이션)
    """
    conn = get_conn()
    cur = conn.cursor()

    sql = """
        SELECT warehouse, brand, item, name, lot, spec, location, qty
        FROM inventory
        WHERE 1=1
    """
    params = []

    if warehouse:
        sql += " AND warehouse = ?"
        params.append(warehouse)

    if q:
        sql += """
          AND (
            item LIKE ? OR name LIKE ? OR brand LIKE ? OR
            lot LIKE ? OR location LIKE ?
          )
        """
        like = f"%{q}%"
        params.extend([like, like, like, like, like])

    sql += " ORDER BY warehouse, location, item"

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    return {
        "재고목록": [
            {
                "장소명": r[0],
                "브랜드": r[1],
                "품번": r[2],
                "품명": r[3],
                "LOT": r[4],
                "규격": r[5],
                "로케이션": r[6],
                "현재고": r[7],
            }
            for r in rows
        ]
    }
