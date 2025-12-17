from fastapi import APIRouter, Query
import sqlite3

router = APIRouter(
    prefix="/inbound",
    tags=["입고"]
)

DB_PATH = "WMS.db"


def get_db():
    return sqlite3.connect(DB_PATH)


@router.post(
    "",
    summary="입고 처리",
    description="입고 처리 후 재고를 증가시키고 작업 이력을 저장합니다."
)
def inbound(
    item_code: str = Query(..., title="품목코드"),
    qty: int = Query(..., title="수량"),
    location: str = Query(..., title="로케이션"),
    remark: str = Query("IN", title="비고")
):
    conn = get_db()
    cur = conn.cursor()

    # 재고 반영
    cur.execute("""
        INSERT INTO inventory (item_code, location, qty)
        VALUES (?, ?, ?)
        ON CONFLICT(item_code, location)
        DO UPDATE SET qty = qty + ?
    """, (item_code, location, qty, qty))

    # 이력 저장
    cur.execute("""
        INSERT INTO history (action_type, item_code, qty, location, remark)
        VALUES ('IN', ?, ?, ?, ?)
    """, (item_code, qty, location, remark))

    conn.commit()
    conn.close()

    return {
        "결과": "입고 완료",
        "품목": item_code,
        "수량": qty,
        "로케이션": location
    }
