from fastapi import APIRouter, Query, HTTPException
import sqlite3

router = APIRouter(
    prefix="/move",
    tags=["재고이동"]
)

DB_PATH = "WMS.db"


def get_db():
    return sqlite3.connect(DB_PATH)


@router.post(
    "",
    summary="재고 이동",
    description="재고를 한 로케이션에서 다른 로케이션으로 이동합니다."
)
def move(
    item_code: str = Query(..., title="품목코드"),
    qty: int = Query(..., title="수량"),
    from_location: str = Query(..., title="출발 로케이션"),
    to_location: str = Query(..., title="도착 로케이션"),
    remark: str = Query("MOVE", title="비고")
):
    conn = get_db()
    cur = conn.cursor()

    # 출발지 재고 확인
    cur.execute("""
        SELECT qty FROM inventory
        WHERE item_code=? AND location=?
    """, (item_code, from_location))

    row = cur.fetchone()
    if not row or row[0] < qty:
        conn.close()
        raise HTTPException(status_code=400, detail="이동할 재고 부족")

    # 출발지 차감
    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?
        WHERE item_code=? AND location=?
    """, (qty, item_code, from_location))

    # 도착지 증가
    cur.execute("""
        INSERT INTO inventory (item_code, location, qty)
        VALUES (?, ?, ?)
        ON CONFLICT(item_code, location)
        DO UPDATE SET qty = qty + ?
    """, (item_code, to_location, qty, qty))

    # 이력 저장
    cur.execute("""
        INSERT INTO history (action_type, item_code, qty, location, remark)
        VALUES ('MOVE', ?, ?, ?, ?)
    """, (item_code, qty, f"{from_location} → {to_location}", remark))

    conn.commit()
    conn.close()

    return {
        "결과": "재고 이동 완료",
        "품목": item_code,
        "수량": qty,
        "이동": f"{from_location} → {to_location}"
    }
