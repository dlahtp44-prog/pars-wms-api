from fastapi import APIRouter, HTTPException
from app.db import get_conn, get_history, log_history

router = APIRouter(prefix="/api/history", tags=["History"])

@router.get("")
def history_list():
    return get_history(300)

@router.post("/rollback")
def rollback(history_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM history WHERE id=?", (history_id,))
    h = cur.fetchone()
    if not h:
        conn.close()
        raise HTTPException(status_code=404, detail="이력 없음")

    tx_type = h["tx_type"]
    wh = h["warehouse"] or ""
    loc = h["location"] or ""
    item_code = h["item_code"] or ""
    lot_no = h["lot_no"] or ""
    qty = float(h["qty"] or 0)

    # 입고 롤백 = 재고에서 qty 차감
    if tx_type in ("IN", "입고"):
        cur.execute("""
            UPDATE inventory
            SET qty = qty - ?
            WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
        """, (qty, wh, loc, item_code, lot_no))
        log_history("ROLLBACK", wh, loc, item_code, lot_no, -qty, f"입고 롤백 #{history_id}")

    # 출고 롤백 = 재고에서 qty 증가
    elif tx_type in ("OUT", "출고"):
        cur.execute("""
            UPDATE inventory
            SET qty = qty + ?
            WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
        """, (qty, wh, loc, item_code, lot_no))
        log_history("ROLLBACK", wh, loc, item_code, lot_no, qty, f"출고 롤백 #{history_id}")

    # 이동 롤백은 현재 구조상 “원복 정보(출발지/도착지)”가 부족하면 자동 복구 불가
    else:
        conn.close()
        raise HTTPException(status_code=400, detail="이동 롤백은 이동 로그에 출발/도착 정보가 있어야 자동 복구 가능합니다.")

    conn.commit()
    conn.close()
    return {"result": "OK", "msg": f"롤백 완료 #{history_id}"}
