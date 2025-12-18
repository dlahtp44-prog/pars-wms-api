from fastapi import APIRouter, HTTPException
from app.db import get_conn, log_history
import json

router = APIRouter(
    prefix="/api/qr",
    tags=["QR"]
)

@router.post(
    "/process",
    summary="QR 스캔 자동 처리",
    description="QR 데이터로 입고/출고/이동 자동 처리"
)
def process_qr(qr_data: str):
    try:
        data = json.loads(qr_data)
    except Exception:
        raise HTTPException(status_code=400, detail="QR 데이터 형식 오류")

    action = data.get("type")      # IN / OUT / MOVE
    item = data.get("item")
    qty = int(data.get("qty", 0))
    location = data.get("location", "")

    conn = get_conn()
    cur = conn.cursor()

    if action == "IN":
        cur.execute("""
            INSERT INTO inventory(item_code, qty)
            VALUES (?, ?)
            ON CONFLICT(item_code)
            DO UPDATE SET qty = qty + ?
        """, (item, qty, qty))

        log_history("입고", item, qty, location)

    elif action == "OUT":
        cur.execute("""
            UPDATE inventory
            SET qty = qty - ?
            WHERE item_code = ?
        """, (qty, item))

        log_history("출고", item, qty, location)

    elif action == "MOVE":
        log_history("이동", item, qty, location)

    else:
        conn.close()
        raise HTTPException(status_code=400, detail="알 수 없는 작업 타입")

    conn.commit()
    conn.close()

    return {
        "결과": "처리 완료",
        "작업": action,
        "품목": item,
        "수량": qty,
        "위치": location
    }
