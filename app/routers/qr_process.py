from fastapi import APIRouter
from app.db import get_conn, log_history
import json

router = APIRouter(prefix="/api", tags=["QR"])

@router.post("/qr/process")
def process_qr(qr_data: str):
    data = json.loads(qr_data)

    action = data.get("type")  # IN / OUT / MOVE
    warehouse = data.get("warehouse", "")
    location = data.get("location", "")
    item_code = data.get("item_code", "")
    item_name = data.get("item_name", "")
    lot_no = data.get("lot_no", "")
    spec = data.get("spec", "")
    qty = float(data.get("qty", 0))
    to_location = data.get("to_location", "")

    conn = get_conn()
    cur = conn.cursor()

    if action == "IN":
        cur.execute("""
            INSERT INTO inventory (warehouse, location, item_code, item_name, lot_no, spec, qty, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(warehouse, location, item_code, lot_no)
            DO UPDATE SET
                item_name=excluded.item_name,
                spec=excluded.spec,
                qty = qty + excluded.qty,
                updated_at=CURRENT_TIMESTAMP
        """, (warehouse, location, item_code, item_name, lot_no, spec, qty))
        conn.commit()
        conn.close()
        log_history("입고", warehouse, location, item_code, item_name, lot_no, spec, qty, "QR")

    elif action == "OUT":
        cur.execute("""
            INSERT INTO inventory (warehouse, location, item_code, item_name, lot_no, spec, qty, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(warehouse, location, item_code, lot_no)
            DO UPDATE SET qty = qty - excluded.qty, updated_at=CURRENT_TIMESTAMP
        """, (warehouse, location, item_code, item_name, lot_no, spec, qty))
        conn.commit()
        conn.close()
        log_history("출고", warehouse, location, item_code, item_name, lot_no, spec, qty, "QR")

    elif action == "MOVE":
        if not to_location:
            conn.close()
            return {"result": "FAIL", "msg": "to_location 필요"}

        # from -
        cur.execute("""
            INSERT INTO inventory (warehouse, location, item_code, lot_no, qty, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(warehouse, location, item_code, lot_no)
            DO UPDATE SET qty = qty - excluded.qty, updated_at=CURRENT_TIMESTAMP
        """, (warehouse, location, item_code, lot_no, qty))

        # to +
        cur.execute("""
            INSERT INTO inventory (warehouse, location, item_code, lot_no, qty, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(warehouse, location, item_code, lot_no)
            DO UPDATE SET qty = qty + excluded.qty, updated_at=CURRENT_TIMESTAMP
        """, (warehouse, to_location, item_code, lot_no, qty))

        conn.commit()
        conn.close()
        log_history("이동", warehouse, location, item_code, item_name, lot_no, spec, qty, f"QR → {to_location}")

    else:
        conn.close()
        return {"result": "FAIL", "msg": "알 수 없는 type"}

    return {"result": "OK"}
