from fastapi import APIRouter
from app.db import get_conn

router = APIRouter(tags=["재고"])

@router.get("/inventory")
def inventory():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    SELECT warehouse, brand, item_code, item_name,
           lot_no, spec, location, qty
    FROM inventory
    """)
    rows = cur.fetchall()
    conn.close()

    return {
        "재고": [
            dict(
                장소명=r[0], 브랜드=r[1], 품번=r[2], 품명=r[3],
                LOT=r[4], 규격=r[5], 로케이션=r[6], 현재고=r[7]
            ) for r in rows
        ]
    }
