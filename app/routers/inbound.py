from fastapi import APIRouter, HTTPException
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/inbound", tags=["Inbound"])

@router.post("/")
def inbound(data: dict):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO inventory
    (warehouse, location, brand, item_code, item_name, lot_no, spec, qty)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(warehouse, location, item_code, lot_no)
    DO UPDATE SET qty = qty + excluded.qty
    """, (
        data["warehouse"], data["location"], data["brand"],
        data["item_code"], data["item_name"],
        data["lot_no"], data["spec"], float(data["qty"])
    ))

    log_history(
        "IN", data["warehouse"], data["location"],
        data["item_code"], data["lot_no"], data["qty"]
    )

    conn.commit()
    conn.close()
    return {"result": "입고 완료"}
