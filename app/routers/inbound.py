from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
from app.db import get_conn, log_history

router = APIRouter(prefix="/api", tags=["입고"])

@router.post("/inbound")
def inbound(
    location_name: str = Form(...),
    location: str = Form(...),
    brand: str = Form(...),
    item_code: str = Form(...),
    item_name: str = Form(...),
    lot_no: str = Form(...),
    spec: str = Form(...),
    qty: int = Form(...)
):
    conn = get_conn()
    cur = conn.cursor()

    # 재고 반영
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
        location_name, location,
        brand, item_code, item_name,
        lot_no, spec, qty
    ))

    # 이력 기록
    log_history("입고", {
        "location_name": location_name,
        "location": location,
        "brand": brand,
        "item_code": item_code,
        "item_name": item_name,
        "lot_no": lot_no,
        "spec": spec,
        "qty": qty
    })

    conn.commit()
    conn.close()

    return RedirectResponse("/inventory-page", status_code=303)
