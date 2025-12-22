# routers/outbound.py
from fastapi import APIRouter, HTTPException
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/outbound", tags=["Outbound"])

@router.post("/")
def outbound(data: dict):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT qty FROM inventory
    WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (
        data["warehouse"], data["location"],
        data["item_code"], data["lot_no"]
    ))

    row = cur.fetchone()
    if not row or row["qty"] < float(data["qty"]):
        raise HTTPException(400, "재고 부족")

    cur.execute("""
    UPDATE inventory
    SET qty = qty - ?
    WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (
        data["qty"], data["warehouse"],
        data["location"], data["item_code"], data["lot_no"]
    ))

    log_history(
        "OUT", data["warehouse"], data["location"],
        data["item_code"], data["lot_no"], -float(data["qty"])
    )

    conn.commit()
    conn.close()
    return {"result": "출고 완료"}
