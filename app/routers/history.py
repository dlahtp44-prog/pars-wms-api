from fastapi import APIRouter
import sqlite3

router = APIRouter(
    prefix="/api/history",
    tags=["이력"]
)

DB_PATH = "WMS.db"


def get_db():
    return sqlite3.connect(DB_PATH)


@router.get(
    "",
    summary="작업 이력 조회",
    description="입고, 출고, 재고 이동 작업 이력을 조회합니다."
)
def history_list():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT action_type, item_code, qty, location, remark, created_at
        FROM history
        ORDER BY created_at DESC
    """)

    rows = cur.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "작업구분": r[0],       # IN / OUT / MOVE
            "품목코드": r[1],
            "수량": r[2],
            "로케이션": r[3],
            "비고": r[4],
            "작업시간": r[5]
        })

    return {
        "이력건수": len(result),
        "작업이력": result
    }


@router.post(
    "/rollback",
    summary="작업 롤백",
    description="최근 작업 1건을 취소(롤백) 처리합니다."
)
def rollback():
    conn = get_db()
    cur = conn.cursor()

    # 가장 최근 이력 1건 조회
    cur.execute("""
        SELECT id, action_type, item_code, qty, location
        FROM history
        ORDER BY created_at DESC
        LIMIT 1
    """)
    row = cur.fetchone()

    if not row:
        conn.close()
        return {"결과": "롤백할 이력이 없습니다."}

    history_id, action, item, qty, loc = row

    # 재고 되돌리기
    if action == "IN":
        cur.execute(
            "UPDATE inventory SET qty = qty - ? WHERE item_code=? AND location=?",
            (qty, item, loc)
        )
    elif action == "OUT":
        cur.execute(
            "UPDATE inventory SET qty = qty + ? WHERE item_code=? AND location=?",
            (qty, item, loc)
        )

    # 이력 삭제
    cur.execute("DELETE FROM history WHERE id=?", (history_id,))
    conn.commit()
    conn.close()

    return {"결과": "최근 작업 1건 롤백 완료"}
