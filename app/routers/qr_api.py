from fastapi import APIRouter
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/qr")

@router.post("/process")
def qr_process(data: dict):
    """
    QR 내용 예:
    IN|A창고|D01-01|728750|H5415|10
    MOVE|A창고|D01-01>D01-02|728750|H5415|5
    """
    parts = data["text"].split("|")
    conn = get_conn()
    cur = conn.cursor()

    if parts[0] == "IN":
        _, wh, loc, code, lot, qty = parts
        qty = float(qty)

        cur.execute("""
            INSERT INTO inventory
            (warehouse, location, item_code, lot_no, qty)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(warehouse, location, item_code, lot_no)
            DO UPDATE SET qty = qty + excluded.qty
        """, (wh, loc, code, lot, qty))

        log_history("IN", wh, loc, code, lot, qty, "QR 입고")

    elif parts[0] == "MOVE":
        _, wh, locs, code, lot, qty = parts
        from_loc, to_loc = locs.split(">")
        qty = float(qty)

        cur.execute("""
            UPDATE inventory
            SET qty = qty - ?
            WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
        """, (qty, wh, from_loc, code, lot))

        cur.execute("""
            INSERT INTO inventory
            (warehouse, location, item_code, lot_no, qty)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(warehouse, location, item_code, lot_no)
            DO UPDATE SET qty = qty + excluded.qty
        """, (wh, to_loc, code, lot, qty))

        log_history("MOVE", wh, from_loc, code, lot, -qty, "QR 이동 출고")
        log_history("MOVE", wh, to_loc, code, lot, qty, "QR 이동 입고")

    conn.commit()
    conn.close()
    return {"result": "OK"}
