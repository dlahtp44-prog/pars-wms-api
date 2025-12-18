from fastapi import APIRouter
from app.db import get_conn, log_history
import json

router = APIRouter(prefix="/api", tags=["QR"])

@router.post("/qr/process")
def process_qr(qr_data: str):
    """
    QR 데이터 기반 자동 처리
    type: IN | OUT | MOVE
    """
    data = json.loads(qr_data)

    action = data.get("type")
    item_code = data.get("item_code")
    qty = int(data.get("qty", 0))
    from_loc = data.get("from_location")
    to_loc = data.get("to_location")

    conn = get_conn()
    cur = conn.cursor()

    # =========================
    # 입고
    # =========================
    if action == "IN":
        cur.execute("""
            INSERT INTO inventory (item_code, qty, location)
            VALUES (?, ?, ?)
            ON CONFLICT(item_code, location)
            DO UPDATE SET qty = qty + ?
        """, (item_code, qty, to_loc, qty))

        log_history("입고", item_code, qty, to_loc)

    # =========================
    # 출고
    # =========================
    elif action == "OUT":
        cur.execute("""
            UPDATE inventory
            SET qty = qty - ?
            WHERE item_code = ? AND location = ?
        """, (qty, item_code, from_loc))

        log_history("출고", item_code, qty, from_loc)

    # =========================
    # 이동
    # =========================
    elif action == "MOVE":
        # 출발지 차감
        cur.execute("""
            UPDATE inventory
            SET qty = qty - ?
            WHERE item_code = ? AND location = ?
        """, (qty, item_code, from_loc))

        # 도착지 증가
        cur.execute("""
            INSERT INTO inventory (item_code, qty, location)
            VALUES (?, ?, ?)
            ON CONFLICT(item_code, location)
            DO UPDATE SET qty = qty + ?
        """, (item_code, qty, to_loc, qty))

        log_history(
            "이동",
            item_code,
            qty,
            f"{from_loc} → {to_loc}"
        )

    else:
        conn.close()
        return {"error": "알 수 없는 작업 타입"}

    conn.commit()
    conn.close()

    return {
        "result": "OK",
        "action": action,
        "item_code": item_code,
        "qty": qty
    }
