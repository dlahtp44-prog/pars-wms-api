from fastapi import APIRouter
from app.db import get_conn, log_history

router = APIRouter(tags=["재고이동"])

@router.post("/move")
def move(item: str, new_location: str, remark: str = ""):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT warehouse, location, qty FROM inventory WHERE item=?
    """, (item,))
    row = cur.fetchone()

    cur.execute("""
        UPDATE inventory SET location=? WHERE item=?
    """, (new_location, item))

    conn.commit()
    conn.close()

    log_history("이동", item, row[2], row[0], new_location, remark)
    return {"result": "이동 완료"}
