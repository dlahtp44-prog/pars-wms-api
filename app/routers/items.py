from fastapi import APIRouter, HTTPException
from app.db import get_conn

router = APIRouter(tags=["품목"])

@router.get("/items/{item}", summary="품목 상세 조회")
def item_detail(item: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT warehouse, brand, item, name, lot, spec, location, qty
        FROM inventory
        WHERE item = ?
    """, (item,))
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="품목 없음")

    return {
        "장소명": row[0],
        "브랜드": row[1],
        "품번": row[2],
        "품명": row[3],
        "LOT": row[4],
        "규격": row[5],
        "로케이션": row[6],
        "현재고": row[7],
    }
