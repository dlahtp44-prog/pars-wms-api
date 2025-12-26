from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db import get_db

router = APIRouter(prefix="/api/outbound")

class OutboundReq(BaseModel):
    item_code: str
    location: str
    lot: str
    quantity: int

@router.post("")
def outbound(req: OutboundReq):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT quantity FROM inventory
        WHERE item_code=? AND location=? AND lot=?
    """, (req.item_code, req.location, req.lot))

    row = cur.fetchone()
    if not row:
        raise HTTPException(400, "재고가 존재하지 않습니다.")

    if row[0] < req.quantity:
        raise HTTPException(400, "출고 수량이 재고보다 많습니다.")

    # 재고 차감
    cur.execute("""
        UPDATE inventory
        SET quantity = quantity - ?
        WHERE item_code=? AND location=? AND lot=?
    """, (req.quantity, req.item_code, req.location, req.lot))

    # 이력
    cur.execute("""
        INSERT INTO history
        (action, item_code, location_from, lot, quantity)
        VALUES ('OUTBOUND', ?, ?, ?, ?)
    """, (req.item_code, req.location, req.lot, req.quantity))

    db.commit()
    return {"result": "ok"}
