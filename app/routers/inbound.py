from fastapi import APIRouter, Form, HTTPException
from datetime import datetime
from app.db import get_db

router = APIRouter()


@router.post("/api/inbound")
async def inbound(
    item_code: str = Form(...),
    item_name: str = Form(...),
    brand: str = Form(...),
    spec: str = Form(...),
    location_code: str = Form(...),
    lot: str = Form(...),
    quantity: int = Form(...)
):
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="quantity must be >= 1")

    conn = get_db()
    cursor = conn.cursor()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1️⃣ 재고 확인
    cursor.execute("""
        SELECT id, quantity
        FROM inventory
        WHERE item_code = ?
          AND location_code = ?
          AND lot = ?
    """, (item_code, location_code, lot))

    row = cursor.fetchone()

    if row:
        inventory_id, old_qty = row
        cursor.execute("""
            UPDATE inventory
            SET quantity = ?, updated_at = ?
            WHERE id = ?
        """, (old_qty + quantity, now, inventory_id))
    else:
        cursor.execute("""
            INSERT INTO inventory (
                item_code, item_name, brand, spec,
                location_code, lot, quantity,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item_code, item_name, brand, spec,
            location_code, lot, quantity,
            now, now
        ))

    # 2️⃣ 이력 기록
    cursor.execute("""
        INSERT INTO history (
            action_type, item_code, location_code,
            lot, quantity, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "INBOUND",
        item_code,
        location_code,
        lot,
        quantity,
        now
    ))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "message": "입고 처리 완료",
        "item_code": item_code,
        "location_code": location_code,
        "lot": lot,
        "quantity": quantity
    }
