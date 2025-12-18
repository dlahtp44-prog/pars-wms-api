from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import RedirectResponse
from app.db import get_conn, log_history

router = APIRouter(prefix="/api", tags=["재고이동"])

@router.post("/move")
def move(
    item_code: str = Form(...),
    lot_no: str = Form(...),
    from_location: str = Form(...),
    to_location: str = Form(...),
    qty: int = Form(...)
):
    conn = get_conn()
    cur = conn.cursor()

    # 출발지 재고
    row = cur.execute("""
        SELECT * FROM inventory
        WHERE item_code=? AND lot_no=? AND location=?
    """, (item_code, lot_no, from_location)).fetchone()

    if not row or row["qty"] < qty:
        conn.close()
        raise HTTPException(400, "이동 재고 부족")

    # 출발지 차감
    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?
        WHERE item_code=? AND lot_no=? AND location=?
    """, (qty, item_code, lot_no, from_location))

    # 도착지 추가
    cur.execute("""
        INSERT INTO inventory (
            location_name, location,
            brand, item_code, item_name,
            lot_no, spec, qty
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(item_code, location, lot_no)
        DO UPDATE SET qty = qty + excluded.qty
    """, (
        row["location_name"],
        to_location,
        row["brand"],
        row["item_code"],
        row["item_name"],
        row["lot_no"],
        row["spec"],
        qty
    ))

    # 이력 (출발 → 도착)
    log_history("이동", {
        **row,
        "location": f"{from_location} → {to_location}",
        "qty": qty
    })

    conn.commit()
    conn.close()

    return RedirectResponse("/inventory-page", status_code=303)
