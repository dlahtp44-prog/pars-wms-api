from fastapi import APIRouter
from app.db import get_conn, log_history
import json

router = APIRouter(tags=["QR"])

@router.post(
    "/qr/process",
    summary="QR 스캔 자동 처리",
    description="QR 코드 데이터를 분석하여 입고/출고/이동을 자동 처리합니다."
)
def process_qr(qr_data: str):
    data = json.loads(qr_data)

    action = data.get("type")
    item = data.get("item")
    qty = int(data.get("qty", 0))
    location = data.get("location", "")

    conn = get_conn()
    cur = conn.cursor()

    if action == "IN":
        cur.execute(
            "INSERT INTO inventory(item, qty) VALUES (?, ?) "
            "ON CONFLICT(item) DO UPDATE SET qty = qty + ?",
            (item, qty, qty)
        )
        log_history("입고", item, qty, location)

    elif action == "OUT":
        cur.execute(
            "UPDATE inventory SET qty = qty - ? WHERE item = ?",
            (qty, item)
        )
        log_history("출고", item, qty, location)

    elif action == "MOVE":
        log_history("이동", item, qty, location)

    else:
        return {"결과": "알 수 없는 작업"}

    conn.commit()
    conn.close()

    return {
        "결과": "처리 완료",
        "작업": action,
        "품목": item,
        "수량": qty,
        "위치": location
    }
