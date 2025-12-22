from fastapi import APIRouter, HTTPException
from app.db import get_conn

router = APIRouter(prefix="/api/history")

@router.post("/rollback/{hid}")
def rollback(hid: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM history WHERE id=?", (hid,))
    h = cur.fetchone()
    if not h:
        raise HTTPException(404, "이력 없음")

    # 반대 처리
    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (
        h["qty"],
        h["warehouse"],
        h["location"],
        h["item_code"],
        h["lot_no"]
    ))

    cur.execute("DELETE FROM history WHERE id=?", (hid,))
    conn.commit()
    conn.close()
    return {"result": "ROLLBACK OK"}
