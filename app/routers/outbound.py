from fastapi import APIRouter, Query, HTTPException
import sqlite3

router = APIRouter(
    prefix="/outbound",
    tags=["출고"]
)

DB_PATH = "WMS.db"


def get_db():
    return sqlite3.connect(DB_PATH)


@router.post(
    "",
    summary="출고 처리",
    description="출고 처리 후 재고를 차감하고 작업 이력을 저장합니다."
)
def outbound(
    item_code: str = Query(..., title="품목코드"),
    qty: int = Query(..., title="수량"),
    location: str = Query(..., title="로케이션"),
    remark: str = Query("OUT", title="비고")
):
    conn = get_db()
    cur = conn.cursor()

    # 재고 확인
    cur.execute("""
        SELECT qty FROM inventory
        WHERE item_code=? AND location=?
    """, (item_code, location))

    row = cur.fetchone()
    if not row or row[0] < qty:
        conn.close()
        raise HTTPException(status_code=400, detail="재고 부족")

    # 재고 차감
    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?
        WHERE item_code=? AND location=?
    """, (qty, item_code, location))

    # 이력 저장
    cur.execute("""
        INSERT INTO history (action_type, item_code, qty, location, remark)
        VALUES ('OUT', ?, ?, ?, ?)
    """, (item_code, qty, location, remark))

    conn.commit()
    conn.close()

    return {
        "결과": "출고 완료",
        "품목": item_code,
        "수량": qty,
        "로케이션": location
    }
