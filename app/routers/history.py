from fastapi import APIRouter, HTTPException
from app.core.database import get_conn

router = APIRouter(prefix="/api/history", tags=["History"])


@router.get("")
def get_history():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM inventory_tx
        ORDER BY id DESC
    """)

    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    conn.close()
    return rows


@router.post("/rollback")
def rollback(tx_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM inventory_tx WHERE id=?", (tx_id,))
    row = cur.fetchone()

    if not row:
        conn.close()
        raise HTTPException(404, "기록 없음")

    qty = float(row["qty"])

    # 재고 수량 보정
    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?
        WHERE item_code=? AND lot_no=? AND location=?
    """, (
        qty,
        row["item_code"],
        row["lot_no"],
        row["location"]
    ))

    # 롤백 이력 추가
    cur.execute("""
        INSERT INTO inventory_tx
        (tx_type, warehouse, location, item_code, lot_no, qty, remark)
        VALUES ('ROLLBACK', ?, ?, ?, ?, ?, ?)
    """, (
        row["warehouse"],
        row["location"],
        row["item_code"],
        row["lot_no"],
        -qty,
        f"ROLLBACK #{tx_id}"
    ))

    conn.commit()
    conn.close()
    return {"result": "OK"}
