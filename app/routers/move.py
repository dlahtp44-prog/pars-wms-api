from fastapi import APIRouter, Query
import sqlite3
from datetime import datetime

router = APIRouter(
    prefix="/move",
    tags=["재고이동"]
)

DB_PATH = "WMS.db"


def get_db():
    return sqlite3.connect(DB_PATH)


@router.post(
    "",
    summary="재고 이동 처리",
    description="재고를 한 위치에서 다른 위치로 이동 처리합니다."
)
def move_stock(
    item_code: str = Query(..., title="품목 코드", description="이동할 품목 코드"),
    from_location: str = Query(..., title="이동 전 위치"),
    to_location: str = Query(..., title="이동 후 위치"),
    remark: str = Query("", title="비고")
):
    conn = get_db()
    cur = conn.cursor()

    # 1️⃣ 기존 재고 확인
    cur.execute(
        """
        SELECT qty FROM inventory
        WHERE item_code = ? AND location = ?
        """,
        (item_code, from_location)
    )
    row = cur.fetchone()

    if not row:
        conn.close()
        return "❌ 이동 전 위치에 재고가 없습니다."

    qty = row[0]

    # 2️⃣ 기존 위치 재고 제거
    cur.execute(
        """
        DELETE FROM inventory
        WHERE item_code = ? AND location = ?
        """,
        (item_code, from_location)
    )

    # 3️⃣ 이동 후 위치 재고 추가
    cur.execute(
        """
        INSERT INTO inventory (item_code, location, qty)
        VALUES (?, ?, ?)
        """,
        (item_code, to_location, qty)
    )

    # 4️⃣ 이력 기록
    cur.execute(
        """
        INSERT INTO history
        (type, item_code, from_location, to_location, qty, remark, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "MOVE",
            item_code,
            from_location,
            to_location,
            qty,
            remark,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    conn.commit()
    conn.close()

    return f"✅ 재고 이동 완료 ({item_code}) : {from_location} → {to_location}"
