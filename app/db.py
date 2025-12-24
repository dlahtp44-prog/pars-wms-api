import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "wms.db"

# =========================
# 공통 연결
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
        PRIMARY KEY (warehouse, location, item_code, lot_no)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT,
        warehouse TEXT,
        location TEXT,
        from_location TEXT,
        to_location TEXT,
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
        SELECT warehouse, location, brand,
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
# 입고
# =========================
def add_inventory(warehouse, location, brand,
                  item_code, item_name, lot_no, spec, qty, remark=""):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO inventory
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(warehouse, location, item_code, lot_no)
    DO UPDATE SET qty = qty + excluded.qty
    """, (
        warehouse, location, brand,
        item_code, item_name, lot_no, spec, qty
    ))

    log_history("IN", warehouse, location, None,
                item_code, lot_no, qty, remark)

    conn.commit()
    conn.close()

# =========================
# 출고
# =========================
def subtract_inventory(warehouse, location,
                       item_code, lot_no, qty, remark=""):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    UPDATE inventory
    SET qty = qty - ?
    WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, warehouse, location, item_code, lot_no))

    log_history("OUT", warehouse, location, None,
                item_code, lot_no, -qty, remark)

    conn.commit()
    conn.close()

# =========================
# 이동
# =========================
def move_inventory(warehouse, from_location, to_location,
                   item_code, lot_no, qty):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    UPDATE inventory
    SET qty = qty - ?
    WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, warehouse, from_location, item_code, lot_no))

    cur.execute("""
    INSERT INTO inventory
    VALUES (?, ?, '', ?, '', ?, '', ?)
    ON CONFLICT(warehouse, location, item_code, lot_no)
    DO UPDATE SET qty = qty + excluded.qty
    """, (
        warehouse, to_location,
        item_code, lot_no, qty
    ))

    log_history("MOVE", warehouse, from_location, to_location,
                item_code, lot_no, qty, "이동")

    conn.commit()
    conn.close()

# =========================
# 이력
# =========================
def get_history(limit=200):
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

def log_history(tx_type, warehouse, location, to_location,
                item_code, lot_no, qty, remark):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO history
    (tx_type, warehouse, location, to_location,
     item_code, lot_no, qty, remark, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tx_type, warehouse, location, to_location,
        item_code, lot_no, qty, remark,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

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
        return

    if h["tx_type"] == "IN":
        subtract_inventory(h["warehouse"], h["location"],
                           h["item_code"], h["lot_no"], h["qty"])
    elif h["tx_type"] == "OUT":
        add_inventory(h["warehouse"], h["location"], "",
                      h["item_code"], "", h["lot_no"], "", abs(h["qty"]))
    elif h["tx_type"] == "MOVE":
        move_inventory(h["warehouse"], h["to_location"],
                       h["location"], h["item_code"], h["lot_no"], h["qty"])

    conn.close()

# =========================
# 대시보드
# =========================
def dashboard_summary():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT IFNULL(SUM(qty),0) FROM inventory")
    total = cur.fetchone()[0]

    cur.execute("""
        SELECT IFNULL(SUM(qty),0)
        FROM history
        WHERE tx_type='IN' AND date(created_at)=date('now')
    """)
    inbound = cur.fetchone()[0]

    cur.execute("""
        SELECT IFNULL(SUM(qty),0)
        FROM history
        WHERE tx_type='OUT' AND date(created_at)=date('now')
    """)
    outbound = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM inventory WHERE qty < 0")
    negative = cur.fetchone()[0]

    conn.close()
    return {
        "inbound_today": inbound,
        "outbound_today": outbound,
        "total_stock": total,
        "negative_stock": negative
    }

# =========================
# 로케이션 QR 조회
# =========================
def get_location_items(location: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT item_code, item_name, lot_no, spec, qty
        FROM inventory
        WHERE location=?
        ORDER BY item_code
    """, (location,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# =========================
# 관리자 인증 (임시)
# =========================
def admin_password_ok(pw: str) -> bool:
    return pw == "admin123"
