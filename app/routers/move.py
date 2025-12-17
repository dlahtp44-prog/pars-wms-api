# app/routers/move.py
from fastapi import APIRouter, HTTPException
from app.db import get_conn, log_history

router = APIRouter(tags=["재고이동"])

@router.post("/move")
def move(
    item: str,
    warehouse: str,
    zone: str,
    rack: str,
    level: str,
    cell: str,
    remark: str = ""
):
    new_location = f"{zone}-{rack}-{level}-{cell}"

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT qty FROM inventory WHERE item=?", (item,))
    row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="품목 없음")

    qty = row[0]

    cur.execute("""
        UPDATE inventory
        SET warehouse=?, zone=?, rack=?, level=?, cell=?
        WHERE item=?
    """, (warehouse, zone, rack, level, cell, item))

    conn.commit()
    conn.close()

    log_history("이동", item, qty, warehouse, new_location, remark)

    return {"result": "이동 완료", "to": new_location}
