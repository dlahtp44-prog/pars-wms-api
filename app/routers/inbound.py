from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
from app.db import get_conn, log_history

router = APIRouter(prefix="/api", tags=["입고"])

@router.post("/inbound")
def inbound(
    item_code: str = Form(...),
    item_name: str = Form(...),
    brand: str = Form(""),
    lot_no: str = Form(""),
    spec: str = Form(""),
    location: str = Form(...),
    qty: int = Form(...)
):
    conn = get_conn()
    cur = conn.cursor()

    # 🔑 inventory 반영 (없으면 INSERT, 있으면 UPDATE)
    cur.execute("""
        INSERT INTO inventory (
            item_code, item_name, brand, lot_no, spec, location, qty
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(item_code, location)
        DO UPDATE SET
            qty = qty + excluded.qty
    """, (
        item_code, item_name, brand, lot_no, spec, location, qty
    ))

    # 작업 이력
    log_history("입고", item_code, qty, location)

    conn.commit()
    conn.close()

    # 작업자 메인으로 이동
    return RedirectResponse("/worker", status_code=303)
