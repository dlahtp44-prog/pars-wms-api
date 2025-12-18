from fastapi import APIRouter
import json
from app.db import get_conn, log_history

router = APIRouter(tags=["QR"])

@router.post("/qr/process")
def process_qr(qr_data: str):
    data = json.loads(qr_data)

    action = data["type"]
    item = data["item"]
    qty = int(data["qty"])
    location = data["location"]

    conn = get_conn()
    cur = conn.cursor()

    if action == "IN":
        cur.execute(
            "UPDATE inventory SET qty = qty + ? WHERE item_code=? AND location=?",
            (qty, item, location)
        )
        log_history("입고(QR)", item, qty, location)

    elif action == "OUT":
        cur.execute(
            "UPDATE inventory SET qty = qty - ? WHERE item_code=? AND location=?",
            (qty, item, location)
        )
        log_history("출고(QR)", item, qty, location)

    elif action == "MOVE":
        log_history("이동(QR)", item, qty, location)

    conn.commit()
    conn.close()

    return {"result": "QR 처리 완료", "action": action}
