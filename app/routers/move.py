from fastapi import APIRouter
from pydantic import BaseModel
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/move", tags=["이동"])

class MoveReq(BaseModel):
    warehouse: str
    from_location: str
    to_location: str
    item_code: str
    lot_no: str
    qty: float

@router.post("")
def move_item(req: MoveReq):
    conn = get_conn()
    cur = conn.cursor()

    # 출발지 차감
    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (
        req.qty,
        req.warehouse,
        req.from_location,
        req.item_code,
        req.lot_no
    ))

    # 도착지 증가
    cur.execute("""
        INSERT INTO inventory
        (warehouse, location, item_code, lot_no, qty)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET qty = qty + excluded.qty
    """, (
        req.warehouse,
        req.to_location,
        req.item_code,
        req.lot_no,
        req.qty
    ))

    log_history(
        "MOVE",
        req.warehouse,
        req.from_location,
        req.item_code,
        req.lot_no,
        -req.qty,
        f"→ {req.to_location}"
    )

    log_history(
        "MOVE",
        req.warehouse,
        req.to_location,
        req.item_code,
        req.lot_no,
        req.qty,
        f"← {req.from_location}"
    )

    conn.commit()
    conn.close()
    return {"result": "OK"}
