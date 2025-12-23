# app/db.py
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "WMS.db"


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

    # UNIQUE (UPSERT 필수)
    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS ux_inventory
    ON inventory (warehouse, location, item_code, lot_no)
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
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
            SUM(qty) as qty
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
        params += [kw, kw, kw, kw]

    sql += """
        GROUP BY warehouse, location, item_code, lot_no
        ORDER BY item_code
    """

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# =========================
# 이력 조회
# =========================
def get_history(limit: int = 300):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM history
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# =========================
# 이력 기록 (공통)
# =========================
def log_history(tx_type, warehouse, location, item_code, lot_no, qty, remark=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO history
        (tx_type, warehouse, location, item_code, lot_no, qty, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        tx_type, warehouse, location,
        item_code, lot_no, qty, remark
    ))
    conn.commit()
    conn.close()


# =========================
# 입고 / 재고 추가
# =========================
def add_inventory(warehouse, location, brand,
                  item_code, item_name, lot_no, spec, qty):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO inventory
        (warehouse, location, brand, item_code, item_name, lot_no, spec, qty)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET
            qty = qty + excluded.qty,
            updated_at = CURRENT_TIMESTAMP
    """, (
        warehouse, location, brand,
        item_code, item_name, lot_no, spec, qty
    ))

    conn.commit()
    conn.close()

    log_history("IN", warehouse, location, item_code, lot_no, qty, "입고")


# =========================
# 출고
# =========================
def outbound_inventory(warehouse, location, item_code, lot_no, qty):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, warehouse, location, item_code, lot_no))

    conn.commit()
    conn.close()

    log_history("OUT", warehouse, location, item_code, lot_no, -qty, "출고")


# =========================
# 이동
# =========================
def move_inventory(warehouse, from_loc, to_loc, item_code, lot_no, qty):
    # 출고
    outbound_inventory(warehouse, from_loc, item_code, lot_no, qty)
    # 입고
    add_inventory(
        warehouse, to_loc, "", item_code, "", lot_no, "", qty
    )
    log_history("MOVE", warehouse, f"{from_loc}->{to_loc}",
                item_code, lot_no, qty, "이동")


# =========================
# 롤백
# =========================
def rollback(tx_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM history WHERE id=?", (tx_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return

    qty = row["qty"]

    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (
        qty,
        row["warehouse"],
        row["location"],
        row["item_code"],
        row["lot_no"]
    ))

    cur.execute("DELETE FROM history WHERE id=?", (tx_id,))
    conn.commit()
    conn.close()


# =========================
# 대시보드
# =========================
def dashboard_summary():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT IFNULL(SUM(qty),0)
        FROM history
        WHERE tx_type='IN'
        AND DATE(created_at)=DATE('now','localtime')
    """)
    inbound = cur.fetchone()[0]

    cur.execute("""
        SELECT IFNULL(SUM(-qty),0)
        FROM history
        WHERE tx_type='OUT'
        AND DATE(created_at)=DATE('now','localtime')
    """)
    outbound = cur.fetchone()[0]

    cur.execute("SELECT IFNULL(SUM(qty),0) FROM inventory")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM inventory WHERE qty < 0")
    negative = cur.fetchone()[0]

    conn.close()
    return inbound, outbound, total, negative


# =========================
# 관리자 비밀번호
# =========================
ADMIN_PASSWORD = "1234"

def admin_password_ok(pw: str):
    return pw == ADMIN_PASSWORD
