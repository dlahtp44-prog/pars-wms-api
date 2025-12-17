from fastapi import APIRouter, HTTPException
from app.db import get_conn, log_history

router = APIRouter(tags=["재고이동"])

@router.post("/move", summary="재고 위치 이동")
def move(item: str, new_location: str, remark: str = ""):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT qty, location FROM inventory WHERE item = ?", (item,))
    row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="품목 없음")

    qty, old_location = row

    cur.execute(
        "UPDATE inventory SET location = ? WHERE item = ?",
        (new_location, item)
    )

    conn.commit()
    conn.close()

    log_history("이동", item, qty, new_location, f"{old_location} → {new_location} {remark}")

    return {
        "result": "이동 완료",
        "item": item,
        "from": old_location,
        "to": new_location
    }
