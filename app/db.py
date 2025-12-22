# app/db.py
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "WMS.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # inventory: 재고
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse TEXT,
        location TEXT,
        brand TEXT,
        item_code TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        qty REAL DEFAULT 0,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 중복 방지용 유니크 인덱스(없으면 생성)
    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS ux_inventory_key
    ON inventory(warehouse, location, item_code, lot_no)
    """)

    # history: 작업 이력
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT,              -- IN / OUT / MOVE / ROLLBACK
        warehouse TEXT,
        location TEXT,             -- MOVE면 "from → to" 같은 표시용
        item_code TEXT,
        item_name TEXT,
        brand TEXT,
        lot_no TEXT,
        spec TEXT,
        qty REAL,
        remark TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

# =========================
# 이력 기록 (공용)
# =========================
def log_history(
    tx_type: str,
    warehouse: str,
    location: str,
    item_code: str,
    item_name: str,
    brand: str,
    lot_no: str,
    spec: str,
    qty: float,
    remark: str = ""
):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO history
        (tx_type, warehouse, location, item_code, item_name, brand, lot_no, spec, qty, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (tx_type, warehouse, location, item_code, item_name, brand, lot_no, spec, qty, remark))
    conn.commit()
    conn.close()

# =========================
# 재고 증감 (공용)
#   - qty 양수: 입고/추가
#   - qty 음수: 출고/차감
# =========================
def add_inventory(
    warehouse: str,
    location: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot_no: str,
    spec: str,
    qty: float
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, qty FROM inventory
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, location, item_code, lot_no))
    row = cur.fetchone()

    if row:
        cur.execute("""
            UPDATE inventory
            SET qty = qty + ?,
                brand=?,
                item_name=?,
                spec=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (qty, brand, item_name, spec, row["id"]))
    else:
        cur.execute("""
            INSERT INTO inventory
            (warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (warehouse, location, brand, item_code, item_name, lot_no, spec, qty))

    conn.commit()
    conn.close()

def get_inventory(warehouse: str | None = None, location: str | None = None, q: str | None = None):
    conn = get_conn()
    cur = conn.cursor()

    sql = """
        SELECT
            warehouse, location, brand, item_code, item_name, lot_no, spec,
            SUM(qty) as qty
        FROM inventory
        WHERE 1=1
    """
    params = []

    if warehouse:
        sql += " AND warehouse=?"
        params.append(warehouse)
    if location:
        sql += " AND location=?"
        params.append(location)
    if q:
        kw = f"%{q}%"
        sql += " AND (item_code LIKE ? OR item_name LIKE ? OR lot_no LIKE ? OR brand LIKE ?)"
        params.extend([kw, kw, kw, kw])

    sql += """
        GROUP BY warehouse, location, item_code, lot_no
        ORDER BY item_code, lot_no
    """

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_history(limit: int = 300):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM history
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# =========================
# MOVE (재고 이동)
# =========================
def move_inventory(
    warehouse: str,
    item_code: str,
    item_name: str,
    brand: str,
    lot_no: str,
    spec: str,
    qty: float,
    from_location: str,
    to_location: str
):
    # 출발지 차감
    add_inventory(warehouse, from_location, brand, item_code, item_name, lot_no, spec, -abs(qty))
    # 도착지 가산
    add_inventory(warehouse, to_location, brand, item_code, item_name, lot_no, spec, abs(qty))

    remark = json.dumps({"from": from_location, "to": to_location}, ensure_ascii=False)
    log_history("MOVE", warehouse, f"{from_location} → {to_location}",
                item_code, item_name, brand, lot_no, spec, abs(qty), remark)

# =========================
# Rollback (이력 id 기준)
#  - IN  -> 재고 -qty
#  - OUT -> 재고 +qty
#  - MOVE -> 역이동
# =========================
def rollback(history_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM history WHERE id=?", (history_id,))
    h = cur.fetchone()
    if not h:
        conn.close()
        return {"ok": False, "msg": "이력 없음"}

    tx = (h["tx_type"] or "").upper()
    wh = h["warehouse"] or ""
    loc = h["location"] or ""
    item_code = h["item_code"] or ""
    item_name = h["item_name"] or ""
    brand = h["brand"] or ""
    lot_no = h["lot_no"] or ""
    spec = h["spec"] or ""
    qty = float(h["qty"] or 0)

    # 이미 롤백한 건 중복 방지(선택)
    if tx == "ROLLBACK":
        conn.close()
        return {"ok": False, "msg": "이미 롤백 이력입니다."}

    if tx == "IN":
        add_inventory(wh, h["location"], brand, item_code, item_name, lot_no, spec, -abs(qty))
    elif tx == "OUT":
        add_inventory(wh, h["location"], brand, item_code, item_name, lot_no, spec, abs(qty))
    elif tx == "MOVE":
        try:
            info = json.loads(h["remark"] or "{}")
            frm = info.get("from", "")
            to = info.get("to", "")
            if frm and to:
                # 역이동
                add_inventory(wh, to, brand, item_code, item_name, lot_no, spec, -abs(qty))
                add_inventory(wh, frm, brand, item_code, item_name, lot_no, spec, abs(qty))
        except Exception:
            pass
    else:
        conn.close()
        return {"ok": False, "msg": f"롤백 불가 타입: {tx}"}

    # 롤백 이력 남김
    log_history("ROLLBACK", wh, loc, item_code, item_name, brand, lot_no, spec, -qty,
                f"ROLLBACK #{history_id}")

    conn.close()
    return {"ok": True, "msg": "롤백 완료"}

# =========================
# 대시보드 요약 (카드/그래프)
# =========================
def dashboard_summary():
    conn = get_conn()
    cur = conn.cursor()

    # 오늘 입고/출고
    cur.execute("""
      SELECT IFNULL(SUM(qty),0) FROM history
      WHERE tx_type='IN' AND DATE(created_at)=DATE('now','localtime')
    """)
    inbound_today = float(cur.fetchone()[0])

    cur.execute("""
      SELECT IFNULL(SUM(qty),0) FROM history
      WHERE tx_type='OUT' AND DATE(created_at)=DATE('now','localtime')
    """)
    outbound_today = float(cur.fetchone()[0])

    # 총 재고
    cur.execute("SELECT IFNULL(SUM(qty),0) FROM inventory")
    total_stock = float(cur.fetchone()[0])

    # 위치 미지정
    cur.execute("""
      SELECT IFNULL(SUM(qty),0) FROM inventory
      WHERE location IS NULL OR TRIM(location)=''
    """)
    no_location = float(cur.fetchone()[0])

    # 음수 재고 건수
    cur.execute("SELECT COUNT(*) FROM inventory WHERE qty < 0")
    negative_count = int(cur.fetchone()[0])

    conn.close()

    return {
        "inbound_today": inbound_today,
        "outbound_today": outbound_today,
        "total_stock": total_stock,
        "no_location": no_location,
        "negative_count": negative_count
    }

# =========================
# 관리자 비번
# =========================
def admin_password_ok(pw: str) -> bool:
    # Railway Variables에 ADMIN_PASSWORD 설정 권장
    expected = os.getenv("ADMIN_PASSWORD", "1234")
    return (pw or "") == expected
