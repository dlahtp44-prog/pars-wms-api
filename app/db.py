import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "WMS.db"


# =====================
# DB 연결
# =====================
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =====================
# DB 초기화
# =====================
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse TEXT,
        location TEXT,
        item_code TEXT,
        lot_no TEXT,
        qty REAL DEFAULT 0,
        UNIQUE(warehouse, location, item_code, lot_no)
    )
    """)

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
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


# =====================
# 재고 조회
# =====================
def get_inventory():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            warehouse,
            location,
            item_code,
            lot_no,
            SUM(qty) AS qty
        FROM inventory
        GROUP BY warehouse, location, item_code, lot_no
        ORDER BY item_code
    """)

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# =====================
# 이력 조회
# =====================
def get_history(limit: int = 200):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM history
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# =====================
# 이력 기록 (공용)
# =====================
def log_history(
    tx_type: str,
    warehouse: str,
    location: str,
    item_code: str,
    lot_no: str,
    qty: float,
    remark: str = ""
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO history
        (tx_type, warehouse, location, item_code, lot_no, qty, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        tx_type,
        warehouse,
        location,
        item_code,
        lot_no,
        qty,
        remark
    ))

    conn.commit()
    conn.close()


# =====================
# 재고 증감 (QR / API 공용)
# =====================
def add_inventory(
    warehouse: str,
    location: str,
    item_code: str,
    lot_no: str,
    qty: float
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO inventory
        (warehouse, location, item_code, lot_no, qty)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET qty = qty + excluded.qty
    """, (
        warehouse,
        location,
        item_code,
        lot_no,
        qty
    ))

    conn.commit()
    conn.close()


# =====================
# 이력 롤백 (관리자)
# =====================
def rollback(history_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM history WHERE id = ?", (history_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False

    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (
        row["qty"],
        row["warehouse"],
        row["location"],
        row["item_code"],
        row["lot_no"]
    ))

    cur.execute("DELETE FROM history WHERE id = ?", (history_id,))
    conn.commit()
    conn.close()
    return True


# =====================
# 대시보드 요약
# =====================
def dashboard_summary():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT IFNULL(SUM(qty),0)
        FROM history
        WHERE tx_type='IN'
          AND date(created_at)=date('now')
    """)
    inbound_today = cur.fetchone()[0]

    cur.execute("""
        SELECT IFNULL(SUM(qty),0)
        FROM history
        WHERE tx_type='OUT'
          AND date(created_at)=date('now')
    """)
    outbound_today = cur.fetchone()[0]

    cur.execute("SELECT IFNULL(SUM(qty),0) FROM inventory")
    total_stock = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM inventory WHERE qty < 0")
    negative = cur.fetchone()[0]

    conn.close()

    return inbound_today, outbound_today, total_stock, negative
