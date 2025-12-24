# app/db.py
import sqlite3
from pathlib import Path
from datetime import datetime
import hashlib
import os

DB_PATH = Path("app/data/wms.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# =========================
# 공통 커넥션
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

    # 재고
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

    # 이력
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT,
        warehouse TEXT,
        location TEXT,
        from_location TEXT,
        to_location TEXT,
        item_code TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        qty REAL,
        remark TEXT,
        created_at TEXT
    )
    """)

    # 관리자 비밀번호 (단일)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        password_hash TEXT
    )
    """)

    # 관리자 기본 비밀번호: 1234
    cur.execute("SELECT COUNT(*) FROM admin")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO admin (id, password_hash) VALUES (1, ?)",
            (hashlib.sha256("1234".encode()).hexdigest(),)
        )

    conn.commit()
    conn.close()

# =========================
# 재고 조회
# =========================
def get_inventory(q: str | None = None):
    conn = get_conn()
    cur = conn.cursor()

    sql = """
    SELECT warehouse, location, brand, item_code, item_name, lot_no, spec, qty
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

    sql += " ORDER BY location, item_code"

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# =========================
# 이력 조회
# =========================
def get_history(limit: int = 500):
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
# 이력 기록
# =========================
def log_history(
    tx_type: str,
    warehouse: str,
    location: str,
    item_code: str,
    item_name: str,
    lot_no: str,
    spec: str,
    qty: float,
    remark: str = "",
    from_location: str = "",
    to_location: str = ""
):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO history
    (tx_type, warehouse, location, from_location, to_location,
     item_code, item_name, lot_no, spec, qty, remark, created_at)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        tx_type, warehouse, location, from_location, to_location,
        item_code, item_name, lot_no, spec, qty, remark,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

# =========================
# 입고
# =========================
def add_inventory(
    warehouse: str,
    location: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot_no: str,
    spec: str,
    qty: float,
    remark: str = "입고"
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO inventory
    (warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at)
    VALUES (?,?,?,?,?,?,?,?,?)
    ON CONFLICT(warehouse, location, item_code, lot_no)
    DO UPDATE SET
        qty = qty + excluded.qty,
        updated_at = excluded.updated_at
    """, (
        warehouse, location, brand, item_code, item_name,
        lot_no, spec, qty, datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    log_history(
        "IN", warehouse, location,
        item_code, item_name, lot_no, spec, qty, remark
    )

# =========================
# 출고
# =========================
def subtract_inventory(
    warehouse: str,
    location: str,
    item_code: str,
    item_name: str,
    lot_no: str,
    spec: str,
    qty: float,
    remark: str = "출고"
):
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

    log_history(
        "OUT", warehouse, location,
        item_code, item_name, lot_no, spec, -qty, remark
    )

# =========================
# 이동
# =========================
def move_inventory(
    warehouse: str,
    item_code: str,
    item_name: str,
    lot_no: str,
    spec: str,
    qty: float,
    from_location: str,
    to_location: str
):
    subtract_inventory(
        warehouse, from_location,
        item_code, item_name, lot_no, spec, qty,
        remark="이동-출"
    )

    add_inventory(
        warehouse, to_location, "",
        item_code, item_name, lot_no, spec, qty,
        remark="이동-입"
    )

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
    AND date(created_at)=date('now')
    """)
    inbound_today = cur.fetchone()[0]

    cur.execute("""
    SELECT IFNULL(SUM(-qty),0)
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

    return {
        "inbound_today": inbound_today,
        "outbound_today": outbound_today,
        "total_stock": total_stock,
        "negative_stock": negative
    }

# =========================
# 관리자
# =========================
def admin_password_ok(password: str) -> bool:
    h = hashlib.sha256(password.encode()).hexdigest()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM admin WHERE password_hash=?", (h,))
    ok = cur.fetchone() is not None
    conn.close()
    return ok

def rollback(tx_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM history WHERE id=?", (tx_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False

    if row["tx_type"] == "IN":
        subtract_inventory(
            row["warehouse"], row["location"],
            row["item_code"], row["item_name"],
            row["lot_no"], row["spec"], row["qty"],
            remark="롤백"
        )
    elif row["tx_type"] == "OUT":
        add_inventory(
            row["warehouse"], row["location"], "",
            row["item_code"], row["item_name"],
            row["lot_no"], row["spec"], -row["qty"],
            remark="롤백"
        )

    cur.execute("DELETE FROM history WHERE id=?", (tx_id,))
    conn.commit()
    conn.close()
    return True
