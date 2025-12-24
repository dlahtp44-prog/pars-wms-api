# app/db.py
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent / "wms.db"


# =========================
# DB 연결
# =========================
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# DB 초기화
# =========================
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # inventory
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        warehouse TEXT,
        location TEXT,
        brand TEXT,
        item_code TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        qty REAL DEFAULT 0,
        updated_at TEXT,
        PRIMARY KEY (warehouse, location, item_code, lot_no)
    )
    """)

    # history
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT,
        warehouse TEXT,
        location TEXT,
        item_code TEXT,
        lot_no TEXT,
        qty REAL,
        remark TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


# =========================
# 재고 조회
# =========================
def get_inventory(q: str | None = None):
    conn = get_conn()
    cur = conn.cursor()

    sql = """
        SELECT
            warehouse, location, brand,
            item_code, item_name, lot_no, spec,
            SUM(qty) AS qty
        FROM inventory
        WHERE 1=1
    """
    params = []

    if q:
        sql += """
        AND (
            item_code LIKE ?
            OR item_name LIKE ?
            OR lot_no LIKE ?
            OR location LIKE ?
        )
        """
        kw = f"%{q}%"
        params.extend([kw, kw, kw, kw])

    sql += """
        GROUP BY warehouse, location, item_code, lot_no
        ORDER BY item_code
    """

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# =========================
# 특정 로케이션 재고
# =========================
def get_location_items(location: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT item_code, item_name, lot_no, spec, SUM(qty) AS qty
        FROM inventory
        WHERE location = ?
        GROUP BY item_code, lot_no
        HAVING qty > 0
        ORDER BY item_code
    """, (location,))

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# =========================
# 이력 기록
# =========================
def log_history(tx_type, warehouse, location, item_code, lot_no, qty, remark=""):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO history
        (tx_type, warehouse, location, item_code, lot_no, qty, remark, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tx_type, warehouse, location,
        item_code, lot_no, qty,
        remark, datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


# =========================
# 입고
# =========================
def add_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, qty):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO inventory
        (warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET
            qty = qty + excluded.qty,
            updated_at = excluded.updated_at
    """, (
        warehouse, location, brand,
        item_code, item_name, lot_no,
        spec, qty, datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    log_history("IN", warehouse, location, item_code, lot_no, qty, "입고")


# =========================
# 출고
# =========================
def subtract_inventory(warehouse, location, item_code, lot_no, qty):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?, updated_at = ?
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (
        qty, datetime.now().isoformat(),
        warehouse, location, item_code, lot_no
    ))

    conn.commit()
    conn.close()

    log_history("OUT", warehouse, location, item_code, lot_no, -qty, "출고")


# =========================
# 이동
# =========================
def move_inventory(warehouse, from_location, to_location,
                   brand, item_code, item_name, lot_no, spec, qty):
    subtract_inventory(warehouse, from_location, item_code, lot_no, qty)
    add_inventory(warehouse, to_location, brand, item_code, item_name, lot_no, spec, qty)

    log_history(
        "MOVE", warehouse, f"{from_location} → {to_location}",
        item_code, lot_no, qty, "이동"
    )


# =========================
# 이력 조회
# =========================
def get_history(limit: int = 300):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM history
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# =========================
# 롤백
# =========================
def rollback(tx_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM history WHERE id=?", (tx_id,))
    h = cur.fetchone()
    if not h:
        conn.close()
        return False

    if h["tx_type"] == "IN":
        subtract_inventory(h["warehouse"], h["location"],
                            h["item_code"], h["lot_no"], h["qty"])
    elif h["tx_type"] == "OUT":
        add_inventory(h["warehouse"], h["location"], "",
                      h["item_code"], "", h["lot_no"], "", abs(h["qty"]))

    cur.execute("DELETE FROM history WHERE id=?", (tx_id,))
    conn.commit()
    conn.close()
    return True


# =========================
# 대시보드
# =========================
def dashboard_summary():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT IFNULL(SUM(qty),0) FROM history
        WHERE tx_type='IN' AND date(created_at)=date('now')
    """)
    inbound_today = cur.fetchone()[0]

    cur.execute("""
        SELECT IFNULL(SUM(qty),0) FROM history
        WHERE tx_type='OUT' AND date(created_at)=date('now')
    """)
    outbound_today = abs(cur.fetchone()[0])

    cur.execute("SELECT IFNULL(SUM(qty),0) FROM inventory")
    total_stock = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM inventory WHERE qty < 0")
    negative_stock = cur.fetchone()[0]

    conn.close()

    return {
        "inbound_today": inbound_today,
        "outbound_today": outbound_today,
        "total_stock": total_stock,
        "negative_stock": negative_stock
    }
